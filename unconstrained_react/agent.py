"""
agent.py

Unconstrained ReAct loop. No schema, no allow-list, no real step limit
(just a generous safety ceiling so a bad run doesn't loop forever).
"""

import re
from shared.tools import TOOLS
from unconstrained_react.prompts import SYSTEM_PROMPT

SAFETY_CEILING = 20  # not a feature — just a leash, unlike constrained_react's MAX_STEPS


def parse_action(model_text):
    """
    Look for a line like 'ACTION: tool_name'.
    Loose on purpose: case-insensitive, tolerant of extra spaces.
    Returns the tool name (str) or None if nothing matched.
    """
    match = re.search(r"ACTION:\s*([a-zA-Z_]+)", model_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def parse_final_answer(model_text):
    """
    Look for 'FINAL ANSWER: tool_name'.
    Returns the tool name (str) or None.
    """
    match = re.search(r"FINAL ANSWER:\s*([a-zA-Z_]+)", model_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def run_unconstrained_agent(campaign, call_model):
    """
    call_model: a function that takes the full conversation (list of
    {"role": ..., "content": ...} dicts) and returns the model's reply text.
    Kept as a parameter so the loop stays provider-agnostic.
    """

    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is the campaign data:\n{campaign}"}
    ]

    log = {
        "campaign_id": campaign["campaign_id"],
        "steps": [],
        "model_calls": 0,
        "final_action": None,
        "hit_safety_ceiling": False,
    }

    for step in range(SAFETY_CEILING):

        # --- Model reasons + (maybe) states an action ---
        reply = call_model(conversation)
        log["model_calls"] += 1
        conversation.append({"role": "assistant", "content": reply})

        # --- Check for a final answer first ---
        final_action = parse_final_answer(reply)
        if final_action:
            log["final_action"] = final_action
            log["steps"].append({"type": "final_answer", "text": reply})
            break

        # --- Otherwise look for a tool call ---
        tool_name = parse_action(reply)

        if tool_name is None:
            # Model didn't clearly ask for a tool or give a final answer.
            # Nudge it instead of crashing.
            observation = (
                "I couldn't find a valid ACTION or FINAL ANSWER in your "
                "last message. Please either call a tool with "
                "'ACTION: tool_name' or give 'FINAL ANSWER: tool_name'."
            )
            log["steps"].append({"type": "unparsed", "text": reply})

        elif tool_name not in TOOLS:
            # Tool not found — tell it and let it keep going.
            observation = (
                f"Tool '{tool_name}' not found. Available tools are: "
                f"{', '.join(TOOLS.keys())}."
            )
            log["steps"].append({"type": "invalid_tool", "tool": tool_name})

        else:
            # Real tool call
            result = TOOLS[tool_name](campaign)
            observation = str(result)
            log["steps"].append({"type": "tool_call", "tool": tool_name, "result": result})

        conversation.append({"role": "user", "content": f"OBSERVATION: {observation}"})

    else:
        # Loop finished without a final answer
        log["hit_safety_ceiling"] = True

    return log


if __name__ == "__main__":
    import json
    from shared.test_cases import CAMPAIGNS
    from unconstrained_react.model_client import call_model

    all_results = []
    results_path = "unconstrained_react/results.json"

    for campaign in CAMPAIGNS:
        try:
            result = run_unconstrained_agent(campaign, call_model)
        except RuntimeError as e:
            # Likely a quota error surfaced from model_client.py.
            # Save what we have so far instead of losing all progress.
            print(f"\nStopped early at {campaign['campaign_id']}: {e}")
            break

        all_results.append(result)

        print(f"\n{result['campaign_id']}: {result['final_action']} "
              f"(model_calls={result['model_calls']}, "
              f"hit_safety_ceiling={result['hit_safety_ceiling']})")

        for i, step in enumerate(result["steps"]):
            print(f"  step {i} ({step['type']}): "
                  f"{step.get('tool', step.get('text', ''))[:80]}")

        # Save after every campaign, not just at the end — so a crash
        # partway through never loses more than the current campaign.
        with open(results_path, "w") as f:
            json.dump(all_results, f, indent=2)

    print(f"\nSaved {len(all_results)}/{len(CAMPAIGNS)} results to {results_path}")
    if len(all_results) < len(CAMPAIGNS):
        print("Re-run this script later (after the quota resets) to pick up "
              "the remaining campaigns — it will overwrite results.json, so "
              "back up the partial file first if you want to keep it.")