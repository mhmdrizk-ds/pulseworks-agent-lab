import sys
import os

# Allow importing from the shared/ folder at the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.test_cases import TEST_CASES


def evaluate_campaign(campaign: dict) -> dict:
    """
    Takes today's campaign data and returns a fixed decision
    based on hard-coded rules. No memory, no reasoning.
    """
    ctr = campaign["ctr"]
    conversions = campaign["conversions"]
    daily_spend = campaign["spend_daily"]
    budget_remaining = campaign["remaining_budget"]

    # Rule 1: No conversions + spending a lot → pause immediately
    if conversions == 0 and daily_spend > 200:
        return {
            "action": "PAUSE_CAMPAIGN",
            "reason": "No conversions despite significant daily spend."
        }

    # Rule 2: Weak click-through rate → reduce budget
    if ctr < 0.5:
        return {
            "action": "REDUCE_BUDGET",
            "reason": f"CTR is low ({ctr}%), reducing daily budget by 20%."
        }

    # Rule 3: Budget almost exhausted → escalate to manager
    if budget_remaining < 100:
        return {
            "action": "ESCALATE_TO_MANAGER",
            "reason": f"Only {budget_remaining} left in budget."
        }

    # Default: everything looks fine
    return {
        "action": "KEEP_RUNNING",
        "reason": "Campaign performance is within acceptable range."
    }


# ---- Run against the shared test cases ----
if __name__ == "__main__":
    for campaign in TEST_CASES:
        result = evaluate_campaign(campaign)
        print(f"Campaign: {campaign['id_campaign']}")
        print(f"  Decision: {result['action']}")
        print(f"  Reason:   {result['reason']}")
        print()