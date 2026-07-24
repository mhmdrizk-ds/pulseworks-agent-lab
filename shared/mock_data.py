"""
Shared mock data for all four agent architectures.
Everyone imports from this file — do not duplicate campaign data
inside individual agent folders.
"""

CAMPAIGNS = [
    {
        "id_campaign": "camp_101",
        "name_client": "Client A",
        "spend_daily": 250,
        "remaining_budget": 3000,
        "clicks": 120,
        "impressions": 15000,
        "conversions": 0,
        "ctr": 0.8,
        "cost_per_conversion": 0,
        "conversion_rate": 0.0,
        "roas": 0.4,
        "audience_fatigue": "Low",
    },
    {
        "id_campaign": "camp_102",
        "name_client": "Client B",
        "spend_daily": 150,
        "remaining_budget": 3000,
        "clicks": 60,
        "impressions": 20000,
        "conversions": 5,
        "ctr": 0.3,
        "cost_per_conversion": 30,
        "conversion_rate": 8.3,
        "roas": 1.2,
        "audience_fatigue": "Medium",
    },
    {
        "id_campaign": "camp_104",
        "name_client": "Client D",
        "spend_daily": 100,
        "remaining_budget": 2000,
        "clicks": 300,
        "impressions": 10000,
        "conversions": 15,
        "ctr": 3.0,
        "cost_per_conversion": 6.6,
        "conversion_rate": 5.0,
        "roas": 3.5,
        "audience_fatigue": "Low",
    },
    {
        "id_campaign": "camp_105",
        "name_client": "Client E",
        "spend_daily": 400,
        "remaining_budget": 2500,
        "clicks": 500,
        "impressions": 20000,
        "conversions": 2,
        "ctr": 2.5,
        "cost_per_conversion": 200,
        "conversion_rate": 0.4,
        "roas": 0.9,
        "audience_fatigue": "Low",
    },
    {
        "id_campaign": "camp_106",
        "name_client": "Client F",
        "spend_daily": 120,
        "remaining_budget": 1800,
        "clicks": 400,
        "impressions": 18000,
        "conversions": 12,
        "ctr": 2.2,
        "cost_per_conversion": 10,
        "conversion_rate": 3.0,
        "roas": 2.0,
        "audience_fatigue": "High",
    },
]

_HISTORY = {
    "camp_101": {"days_underperforming": 1, "trend": "declining"},
    "camp_102": {"days_underperforming": 2, "trend": "declining"},
    "camp_104": {"days_underperforming": 0, "trend": "improving"},
    "camp_105": {"days_underperforming": 1, "trend": "stable"},
    "camp_106": {"days_underperforming": 4, "trend": "declining"},
}


def get_campaign_history(campaign_id: str) -> dict:
    """
    The 'hidden' tool. Only Constrained ReAct (and Unconstrained LLM,
    if it chooses to) should call this. Reactive and Routing never do.
    """
    return _HISTORY.get(
        campaign_id, {"days_underperforming": 0, "trend": "stable"}
    )