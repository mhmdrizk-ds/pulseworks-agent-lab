"""
Shared campaign data for all agent architectures.

Reactive Agent:
    Uses only the fields in CAMPAIGNS.

Routing Agent:
    Uses only the fields in CAMPAIGNS.

Unconstrained ReAct:
    May use tools to access hidden history.

Constrained ReAct:
    Same as above, but only through the allowed tools.
"""

CAMPAIGNS = [

    # -------------------------------------------------
    # camp_101 : Healthy Campaign
    # Expected:
    # Reactive -> Continue
    # Routing -> Healthy
    # ReAct -> Continue
    # -------------------------------------------------
    {
        "campaign_id": "camp_101",
        "client": "TechNova",

        "ctr": 2.8,
        "conversion_rate": 5.2,
        "roas": 4.5,

        "daily_spend": 180,
        "remaining_budget": 4200,

        "audience_fatigue": "Low",
        "creative_performance": "Excellent"
    },

    # -------------------------------------------------
    # camp_102 : Low CTR only
    # -------------------------------------------------
    {
        "campaign_id": "camp_102",
        "client": "FreshBites",

        "ctr": 0.6,
        "conversion_rate": 3.4,
        "roas": 3.8,

        "daily_spend": 220,
        "remaining_budget": 2500,

        "audience_fatigue": "Low",
        "creative_performance": "Good"
    },

    # -------------------------------------------------
    # camp_103 : Poor ROAS
    # -------------------------------------------------
    {
        "campaign_id": "camp_103",
        "client": "FitLife",

        "ctr": 2.1,
        "conversion_rate": 2.2,
        "roas": 0.7,

        "daily_spend": 320,
        "remaining_budget": 1800,

        "audience_fatigue": "Medium",
        "creative_performance": "Good"
    },

    # -------------------------------------------------
    # camp_104 : Audience Fatigue
    # -------------------------------------------------
    {
        "campaign_id": "camp_104",
        "client": "StyleHub",

        "ctr": 2.3,
        "conversion_rate": 3.7,
        "roas": 3.5,

        "daily_spend": 200,
        "remaining_budget": 2700,

        "audience_fatigue": "High",
        "creative_performance": "Good"
    },

    # -------------------------------------------------
    # camp_105 : Poor Creative
    # -------------------------------------------------
    {
        "campaign_id": "camp_105",
        "client": "TravelGo",

        "ctr": 0.8,
        "conversion_rate": 2.8,
        "roas": 2.4,

        "daily_spend": 190,
        "remaining_budget": 2200,

        "audience_fatigue": "Low",
        "creative_performance": "Poor"
    },

    # -------------------------------------------------
    # camp_106 : Budget almost exhausted
    # -------------------------------------------------
    {
        "campaign_id": "camp_106",
        "client": "EcoHome",

        "ctr": 2.0,
        "conversion_rate": 3.0,
        "roas": 2.7,

        "daily_spend": 250,
        "remaining_budget": 80,

        "audience_fatigue": "Low",
        "creative_performance": "Good"
    },

    # -------------------------------------------------
    # camp_107 : Looks good today
    # Hidden history is very bad.
    # This is the important ReAct example.
    # -------------------------------------------------
    {
        "campaign_id": "camp_107",
        "client": "SmartWear",

        "ctr": 2.4,
        "conversion_rate": 4.0,
        "roas": 3.2,

        "daily_spend": 230,
        "remaining_budget": 2800,

        "audience_fatigue": "Low",
        "creative_performance": "Good"
    },

    # -------------------------------------------------
    # camp_108 : Everything is bad
    # -------------------------------------------------
    {
        "campaign_id": "camp_108",
        "client": "FoodExpress",

        "ctr": 0.3,
        "conversion_rate": 0.0,
        "roas": 0.4,

        "daily_spend": 420,
        "remaining_budget": 1200,

        "audience_fatigue": "High",
        "creative_performance": "Poor"
    },

    # -------------------------------------------------
    # camp_109 : Mixed signals
    # Great CTR
    # Bad ROAS
    # High Audience Fatigue
    # Requires reasoning.
    # -------------------------------------------------
    {
        "campaign_id": "camp_109",
        "client": "LuxuryLiving",

        "ctr": 3.2,
        "conversion_rate": 1.1,
        "roas": 0.9,

        "daily_spend": 350,
        "remaining_budget": 1500,

        "audience_fatigue": "High",
        "creative_performance": "Excellent"
    },

    # -------------------------------------------------
    # camp_110 : Normal campaign
    # -------------------------------------------------
    {
        "campaign_id": "camp_110",
        "client": "GreenGarden",

        "ctr": 1.9,
        "conversion_rate": 2.8,
        "roas": 2.9,

        "daily_spend": 170,
        "remaining_budget": 2400,

        "audience_fatigue": "Medium",
        "creative_performance": "Average"
    }

]

# =====================================================
# Hidden campaign history
# Accessible ONLY through get_campaign_history()
# =====================================================

_HISTORY = {

    "camp_101": {
        "days_underperforming": 0,
        "trend": "Improving"
    },

    "camp_102": {
        "days_underperforming": 3,
        "trend": "Declining"
    },

    "camp_103": {
        "days_underperforming": 4,
        "trend": "Declining"
    },

    "camp_104": {
        "days_underperforming": 2,
        "trend": "Stable"
    },

    "camp_105": {
        "days_underperforming": 3,
        "trend": "Declining"
    },

    "camp_106": {
        "days_underperforming": 0,
        "trend": "Stable"
    },

    # IMPORTANT CASE
    "camp_107": {
        "days_underperforming": 8,
        "trend": "Strongly Declining"
    },

    "camp_108": {
        "days_underperforming": 10,
        "trend": "Strongly Declining"
    },

    "camp_109": {
        "days_underperforming": 5,
        "trend": "Declining"
    },

    "camp_110": {
        "days_underperforming": 1,
        "trend": "Stable"
    }

}


def get_campaign_history(campaign_id: str):
    """
    Hidden history.
    Reactive and Routing should NEVER call this.
    ReAct agents may use it through a tool.
    """

    return _HISTORY.get(
        campaign_id,
        {
            "days_underperforming": 0,
            "trend": "Stable"
        }
    )