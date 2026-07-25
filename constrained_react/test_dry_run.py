"""
Runs the constrained ReAct loop with a SCRIPTED fake call_model instead
of a real API call. No tokens spent, no network calls made.

Same idea as unconstrained_react/test_dry_run.py, but these scenarios are
chosen to exercise the three constraints specifically: schema validation,
the tool allow-list, and MAX_STEPS.

Run with:
    python -m constrained_react.test_dry_run
"""

from constrained_react.agent import run_constrained_agent, MAX_STEPS


def make_scripted_call_model(scripted_replies):
    """
    Returns a call_model(conversation) function that ignores the real
    conversation and just returns the next canned reply each time it's
    called, in order. Raises if the loop asks for more replies than we
    scripted (a signal the loop ran longer than expected).
    """
    replies = iter(scripted_replies)

    def call_model(conversation):
        try:
            return next(replies)
        except StopIteration:
            raise AssertionError(
                "Loop asked for more model replies than were scripted — "
                "check whether it's looping when it shouldn't be."
            )

    return call_model


CAMPAIGN = {
    "campaign_id": "camp_107",
    "client": "SmartWear",
    "ctr": 2.4,
    "conversion_rate": 4.0,
    "roas": 3.2,
    "daily_spend": 230,
    "remaining_budget": 2800,
    "audience_fatigue": "Low",
    "creative_performance": "Good"
}


# ==========================================================
# Scenario 1: Normal flow — checks history, then decides.
# Verifies: schema-valid JSON parses correctly, tool call executes,
# observation feeds back in, final_answer ends the loop cleanly.
# Same shape as unconstrained_react's Scenario 1, for direct comparison.
# ==========================================================
scenario_1 = [
    '{"thought": "Surface metrics look healthy, but I should check '
    'history before trusting that.", "action": "get_campaign_history", '
    '"is_final": false}',

    '{"thought": "This campaign has been declining for 8 days despite '
    'looking fine today. The trend is misleading on the surface.", '
    '"action": "final_answer", "answer": "Recommend decreasing budget - '
    '8-day decline outweighs today\'s healthy surface metrics.", '
    '"is_final": true}',
]

# ==========================================================
# Scenario 2: Model requests a tool NOT in the allow-list.
# Verifies: the disallowed action is rejected by Pydantic's field
# validator on AgentStep itself — it never becomes a valid step, so it
# never reaches the tool-dispatch code at all. This is caught one layer
# earlier than the defensive "if step.action not in TOOLS" check further
# down in agent.py (that check is a backup that should rarely, if ever,
# actually trigger — the schema is the real gate).
# The rejection is absorbed inside _get_validated_step's retry loop, so
# it costs one extra model call but never surfaces as its own trace
# entry. Contrast with the unconstrained agent's Scenario 2, which lets
# the hallucinated call through as a normal "tool not found" observation
# with no schema layer to stop it before that point.
# ==========================================================
scenario_2 = [
    '{"thought": "Let me check the recent trend.", '
    '"action": "check_recent_trend", "is_final": false}',

    '{"thought": "That tool is not allowed. I will use the real one '
    'instead.", "action": "get_campaign_history", "is_final": false}',

    '{"thought": "Confirmed: 8 days of decline. This is not sustainable.", '
    '"action": "escalate_to_manager", "is_final": false}',

    '{"thought": "Escalated. Wrapping up.", "action": "final_answer", '
    '"answer": "Escalated to manager due to prolonged decline.", '
    '"is_final": true}',
]

# ==========================================================
# Scenario 3: Model's first reply is not valid JSON at all.
# Verifies: _get_validated_step retries with a correction message
# instead of crashing or guessing, and recovers within
# STEP_RETRY_ATTEMPTS. Contrast with the unconstrained agent's
# Scenario 3, which just nudges and moves on with no real validation.
# ==========================================================
scenario_3 = [
    "Hmm, I'm not sure what to check first for this campaign.",

    '{"thought": "Let me check audience fatigue.", '
    '"action": "check_audience_fatigue", "is_final": false}',

    '{"thought": "Fatigue is low, that is not the issue. Continue.", '
    '"action": "final_answer", "answer": "Continue as-is, nothing here '
    'warrants a change.", "is_final": true}',
]

# ==========================================================
# Scenario 4: Model never gives a final_answer — just keeps
# calling info tools until MAX_STEPS runs out.
# Verifies: the loop is physically capped at MAX_STEPS and forces
# an escalate_to_manager call itself, rather than looping forever
# like the unconstrained agent would (its only limit is the much
# higher, non-enforced SAFETY_CEILING).
# ==========================================================
scenario_4 = [
    '{"thought": "Checking history.", "action": "get_campaign_history", "is_final": false}',
    '{"thought": "Checking creative.", "action": "check_creative_performance", "is_final": false}',
    '{"thought": "Checking fatigue.", "action": "check_audience_fatigue", "is_final": false}',
    '{"thought": "Checking history again.", "action": "get_campaign_history", "is_final": false}',
    '{"thought": "Checking creative again.", "action": "check_creative_performance", "is_final": false}',
]


def run_scenario(name, scripted_replies):
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    fake_call_model = make_scripted_call_model(scripted_replies)
    result = run_constrained_agent(CAMPAIGN, fake_call_model)

    print(f"final_action:      {result['final_action']}")
    print(f"model_calls:       {result['model_calls']}")
    print(f"forced_escalation: {result['forced_escalation']}")
    print("steps:")
    for step in result["steps"]:
        detail = step.get("tool", step.get("action", step.get("text", "")))
        print(f"  - {step['type']}: {detail}")

    return result


if __name__ == "__main__":
    r1 = run_scenario("Scenario 1: Normal flow", scenario_1)
    assert "decreasing budget" in r1["final_action"].lower()
    assert r1["model_calls"] == 2
    assert r1["forced_escalation"] is False

    r2 = run_scenario("Scenario 2: Disallowed tool name blocked", scenario_2)
    assert r2["final_action"] == "Escalated to manager due to prolonged decline."
    # The disallowed action must never have been executed as a real tool call,
    # and must never appear as an accepted step - it should be invisible in
    # the trace, having been rejected and retried before ever becoming a step.
    assert not any(s.get("tool") == "check_recent_trend" for s in r2["steps"])
    assert not any(s.get("action") == "check_recent_trend" for s in r2["steps"])
    # The rejection-and-retry costs one extra model call beyond the 3 "real"
    # steps (get_campaign_history -> escalate_to_manager -> final_answer).
    assert r2["model_calls"] == 4
    assert r2["forced_escalation"] is False

    r3 = run_scenario("Scenario 3: Invalid JSON, then recovers", scenario_3)
    assert "continue as-is" in r3["final_action"].lower()
    # confirms the retry path actually fired at least once
    assert r3["model_calls"] >= len(scenario_3)

    r4 = run_scenario("Scenario 4: MAX_STEPS exhausted, forced escalation", scenario_4)
    assert r4["forced_escalation"] is True
    assert r4["final_action"] == "escalate_to_manager"
    assert any(s["type"] == "forced_escalation_max_steps" for s in r4["steps"])
    print(f"\n(MAX_STEPS is set to {MAX_STEPS} — loop stopped itself instead of running forever)")

    print("\nAll dry-run scenarios passed. Loop logic looks correct.")
