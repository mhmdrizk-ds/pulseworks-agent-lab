import sys
import os

# Allow importing from shared/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.tools import (
    pause_campaign,
    refresh_creative,
    decrease_budget,
    change_audience,
    escalate_to_manager,
    continue_campaign,
)

from shared.test_cases import TEST_CASES


def evaluate_campaign(campaign: dict) -> dict:
    """
    Reactive Agent

    Uses fixed if/else rules only.
    No LLM.
    No reasoning.
    """

    ctr = campaign["ctr"]
    conversion_rate = campaign["conversion_rate"]
    roas = campaign["roas"]
    audience_fatigue = campaign["audience_fatigue"]
    remaining_budget = campaign["remaining_budget"]

    # Priority 1
    if conversion_rate == 0 and roas < 1:
        return pause_campaign(campaign)

    # Priority 2
    if audience_fatigue == "High":
        return change_audience(campaign)

    # Priority 3
    if ctr < 1.0:
        return refresh_creative(campaign)

    # Priority 4
    if roas < 1.5:
        return decrease_budget(campaign)

    # Priority 5
    if remaining_budget < 100:
        return escalate_to_manager(campaign)

    # Otherwise
    return continue_campaign(campaign)


def main():

    print("=" * 70)
    print("Reactive Marketing Agent")
    print("=" * 70)

    for i, campaign in enumerate(TEST_CASES, start=1):

        result = evaluate_campaign(campaign)

        print(f"\nCampaign {i}")
        print("-" * 40)

        print("Input:")
        for k, v in campaign.items():
            print(f"  {k}: {v}")

        print("\nDecision:")
        print(f"  Action : {result['action']}")
        print(f"  Reason : {result['reason']}")

        print("-" * 40)


if __name__ == "__main__":
    main()