"""
Runs the unconstrained ReAct loop with a SCRIPTED fake call_model instead
of a real API call. No tokens spent, no network calls made.

Each scenario below is a canned list of "model replies" fed to the loop
one at a time, in order. This lets you verify the loop's control flow
(parsing, tool dispatch, observation feeding, termination) is correct
before spending real API calls on it.

Run with:
    python -m unconstrained_react.test_dry_run
"""

from unconstrained_react.agent import run_unconstrained_agent


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
# Verifies: tool call parses correctly, observation feeds back in,
# final answer parses correctly, loop stops on its own.
# ==========================================================
scenario_1 = [
    "Surface metrics look healthy, but I should check history before "
    "trusting that.\nACTION: get_campaign_history",

    "This campaign has been declining for 8 days despite looking fine "
    "today. That's a real problem.\nFINAL ANSWER: decrease_budget\n"
    "The surface metrics are misleading; the trend says otherwise.",
]

# ==========================================================
# Scenario 2: Model hallucinates a tool name that doesn't exist.
# Verifies: "tool not found" observation is returned instead of a crash,
# and the loop successfully continues afterward.
# ==========================================================
scenario_2 = [
    "Let me check the recent trend.\nACTION: check_recent_trend",

    "Oh, that tool doesn't exist. Let me use the real one instead.\n"
    "ACTION: get_campaign_history",

    "Confirmed: 8 days of decline.\nFINAL ANSWER: escalate_to_manager\n"
    "This has been declining too long to leave as-is.",
]

# ==========================================================
# Scenario 3: Model's reply doesn't match the expected format at all
# (no ACTION, no FINAL ANSWER — just rambling).
# Verifies: parser correctly returns None for both, loop sends a nudge
# instead of crashing, and recovers on the next turn.
# ==========================================================
scenario_3 = [
    "Hmm, I'm not sure what to check first for this campaign.",

    "Let me check the audience fatigue level.\nACTION: check_audience_fatigue",

    "Fatigue is low, that's not the issue. I'll go with continuing it.\n"
    "FINAL ANSWER: continue_campaign\nNothing here warrants a change.",
]


def run_scenario(name, scripted_replies):
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    fake_call_model = make_scripted_call_model(scripted_replies)
    result = run_unconstrained_agent(CAMPAIGN, fake_call_model)

    print(f"final_action:       {result['final_action']}")
    print(f"model_calls:        {result['model_calls']}")
    print(f"hit_safety_ceiling: {result['hit_safety_ceiling']}")
    print("steps:")
    for step in result["steps"]:
        print(f"  - {step['type']}: {step.get('tool', step.get('text', ''))[:60]}")

    return result


if __name__ == "__main__":
    r1 = run_scenario("Scenario 1: Normal flow", scenario_1)
    assert r1["final_action"] == "decrease_budget"
    assert r1["model_calls"] == 2
    assert r1["hit_safety_ceiling"] is False

    r2 = run_scenario("Scenario 2: Hallucinated tool name", scenario_2)
    assert r2["final_action"] == "escalate_to_manager"
    assert any(s["type"] == "invalid_tool" for s in r2["steps"])

    r3 = run_scenario("Scenario 3: Unparseable reply", scenario_3)
    assert r3["final_action"] == "continue_campaign"
    assert any(s["type"] == "unparsed" for s in r3["steps"])

    print("\nAll dry-run scenarios passed. Loop logic looks correct.")