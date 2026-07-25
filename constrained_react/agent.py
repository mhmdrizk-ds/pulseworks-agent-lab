"""
constrained_react/agent.py

Constrained ReAct loop. Same shape as unconstrained_react/agent.py, but
every step is boxed in on three sides:

  1. SCHEMA     each step must validate against AgentStep (Pydantic) below.
                Invalid JSON or a schema violation triggers a bounded
                retry (STEP_RETRY_ATTEMPTS), not a guess.
  2. ALLOW-LIST "action" must be a key in TOOLS (from shared/tools.py) or
                the literal string "final_answer" — nothing else is ever
                executed. This is enforced twice: once by the Pydantic
                validator, once again defensively before execution.
  3. MAX_STEPS  hard cap below. If it's reached without a final_answer,
                we force an escalate_to_manager call if that tool exists,
                rather than silently stopping like the unconstrained loop
                would (hit_safety_ceiling there just gives up).

Reuses unconstrained_react/model_client.py unchanged — call_model() is
provider-agnostic and doesn't care which loop calls it. (Longer-term this
file probably belongs in shared/, since both agents depend on it now —
worth raising with the team, not something to fix silently in this PR.)
"""

import json

from pydantic import BaseModel, field_validator
from shared.tools import TOOLS
from constrained_react.prompts import SYSTEM_PROMPT

MAX_STEPS = 5  # <-- hard cap, easy to find
STEP_RETRY_ATTEMPTS = 2  # bounded retries per step when the model's output fails validation

ALLOWED_ACTIONS = set(TOOLS.keys()) | {"final_answer"}  # <-- the allow-list


class AgentStep(BaseModel):
    thought: str
    action: str
    answer: str | None = None
    is_final: bool = False

    @field_validator("action")
    @classmethod
    def action_must_be_allowed(cls, v):
        if v not in ALLOWED_ACTIONS:
            raise ValueError(
                f"action '{v}' is not in the allow-list: {sorted(ALLOWED_ACTIONS)}"
            )
        return v


def _extract_json(text):
    """
    Try to parse text as JSON directly; if the model wrapped it in prose
    or fences anyway, fall back to grabbing the first {...} block.
    Returns a dict, or raises ValueError if nothing parseable is found.
    """
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])  # let this raise if still bad
        raise ValueError("no JSON object found in model output")


def _get_validated_step(conversation, call_model, log):
    """
    Calls the model and validates the reply against AgentStep.
    On failure, appends a correction message to a LOCAL copy of the
    conversation and retries, up to STEP_RETRY_ATTEMPTS times.
    Returns (AgentStep, raw_reply) on success, or (None, last_raw_reply)
    if validation never succeeded.
    """
    local_conversation = list(conversation)
    last_raw = None

    for attempt in range(STEP_RETRY_ATTEMPTS):
        reply = call_model(local_conversation)
        log["model_calls"] += 1
        last_raw = reply

        try:
            data = _extract_json(reply)
            step = AgentStep(**data)
            return step, reply
        except Exception as e:
            local_conversation = local_conversation + [
                {"role": "assistant", "content": reply},
                {
                    "role": "user",
                    "content": (
                        f"Your last response was invalid: {e}. "
                        f"Respond again with ONLY a JSON object matching the "
                        f"required schema (thought, action, answer, is_final)."
                    ),
                },
            ]

    return None, last_raw


def run_constrained_agent(campaign, call_model):
    """
    call_model: same provider-agnostic function signature as the
    unconstrained agent — list of {"role", "content"} dicts in, reply
    text out.
    """

    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT.format(max_steps=MAX_STEPS)},
        {"role": "user", "content": f"Here is the campaign data:\n{campaign}"},
    ]

    log = {
        "campaign_id": campaign["campaign_id"],
        "steps": [],
        "model_calls": 0,
        "final_action": None,
        "forced_escalation": False,
    }

    for step_num in range(1, MAX_STEPS + 1):
        step, raw_reply = _get_validated_step(conversation, call_model, log)

        if step is None:
            # Validation failed every attempt — don't guess, don't crash.
            # Force an escalation if the tool exists, otherwise log and stop.
            log["steps"].append({"type": "validation_failed", "text": raw_reply})
            if "escalate_to_manager" in TOOLS:
                result = TOOLS["escalate_to_manager"](campaign)
                log["final_action"] = "escalate_to_manager"
                log["forced_escalation"] = True
                log["steps"].append({"type": "forced_escalation", "result": result})
            break

        conversation.append({"role": "assistant", "content": raw_reply})
        log["steps"].append({"type": "step", "thought": step.thought, "action": step.action})

        if step.action == "final_answer" or step.is_final:
            log["final_action"] = step.answer or "final_answer (no answer text given)"
            log["steps"].append({"type": "final_answer", "text": step.answer})
            break

        # Defensive re-check — the Pydantic validator should already have
        # caught this, but never execute anything outside TOOLS regardless.
        if step.action not in TOOLS:
            log["steps"].append({"type": "blocked_action", "action": step.action})
            observation = (
                f"Action '{step.action}' is not permitted. Available tools: "
                f"{', '.join(sorted(TOOLS.keys()))}."
            )
        else:
            result = TOOLS[step.action](campaign)
            observation = str(result)
            log["steps"].append({"type": "tool_call", "tool": step.action, "result": result})

        conversation.append({"role": "user", "content": f"OBSERVATION: {observation}"})

    else:
        # MAX_STEPS exhausted without a final_answer ever firing.
        if log["final_action"] is None and "escalate_to_manager" in TOOLS:
            result = TOOLS["escalate_to_manager"](campaign)
            log["final_action"] = "escalate_to_manager"
            log["forced_escalation"] = True
            log["steps"].append({"type": "forced_escalation_max_steps", "result": result})

    return log


if __name__ == "__main__":
    import json as _json
    from shared.test_cases import CAMPAIGNS
    from unconstrained_react.model_client import call_model

    all_results = []
    results_path = "constrained_react/results.json"

    for campaign in CAMPAIGNS:
        try:
            result = run_constrained_agent(campaign, call_model)
        except RuntimeError as e:
            # Same quota-error handling as the unconstrained loop.
            print(f"\nStopped early at {campaign['campaign_id']}: {e}")
            break

        all_results.append(result)

        print(f"\n{result['campaign_id']}: {result['final_action']} "
              f"(model_calls={result['model_calls']}, "
              f"forced_escalation={result['forced_escalation']})")

        for i, step in enumerate(result["steps"]):
            print(f"  step {i} ({step['type']}): "
                  f"{step.get('tool', step.get('action', step.get('text', '')))}")

        with open(results_path, "w") as f:
            _json.dump(all_results, f, indent=2)

    print(f"\nSaved {len(all_results)}/{len(CAMPAIGNS)} results to {results_path}")
    if len(all_results) < len(CAMPAIGNS):
        print("Re-run this script later (after the quota resets) to pick up "
              "the remaining campaigns — it will overwrite results.json, so "
              "back up the partial file first if you want to keep it.")
