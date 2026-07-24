def evaluate_campaign(campaign: dict) -> dict:
    
    ctr = campaign["ctr"]
    conversions = campaign["conversions"]
    daily_spend = campaign["daily_spend"]
    budget_remaining = campaign["budget_remaining"]
    cost_per_conversion = campaign["cost_per_conversion"]

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


# ---- Test cases ----
if __name__ == "__main__":
    test_campaigns = [
        {
            "campaign_id": "camp_101",
            "daily_spend": 250,
            "budget_remaining": 3000,
            "clicks": 120,
            "impressions": 15000,
            "conversions": 0,
            "ctr": 0.8,
            "cost_per_conversion": 0
        },
        {
            "campaign_id": "camp_102",
            "daily_spend": 150,
            "budget_remaining": 3000,
            "clicks": 60,
            "impressions": 20000,
            "conversions": 5,
            "ctr": 0.3,
            "cost_per_conversion": 30
        },
        {
            "campaign_id": "camp_103",
            "daily_spend": 100,
            "budget_remaining": 80,
            "clicks": 200,
            "impressions": 10000,
            "conversions": 10,
            "ctr": 2.0,
            "cost_per_conversion": 10
        },
        {
            "campaign_id": "camp_104",
            "daily_spend": 100,
            "budget_remaining": 2000,
            "clicks": 300,
            "impressions": 10000,
            "conversions": 15,
            "ctr": 3.0,
            "cost_per_conversion": 6.6
        },
        # Tricky case: good CTR but very high cost_per_conversion
        # (the case the Reactive agent CANNOT catch)
        {
            "campaign_id": "camp_105",
            "daily_spend": 400,
            "budget_remaining": 2500,
            "clicks": 500,
            "impressions": 20000,
            "conversions": 2,
            "ctr": 2.5,
            "cost_per_conversion": 200
        },
    ]

    for campaign in test_campaigns:
        result = evaluate_campaign(campaign)
        print(f"Campaign: {campaign['campaign_id']}")
        print(f"  Decision: {result['action']}")
        print(f"  Reason:   {result['reason']}")
        print()