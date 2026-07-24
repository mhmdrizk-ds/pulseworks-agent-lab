"""
Shared mock data for all four agent architectures.
Everyone imports from this file — do not duplicate campaign data
inside individual agent folders.
"""

# Today's campaign reports — available to ALL architectures
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
    },
]

# Hidden history data — NOT part of the daily report.
# Only accessible through get_campaign_history() as a "tool".
_HISTORY = {
    "camp_101": {"days_underperforming": 1, "trend": "declining"},
    "camp_102": {"days_underperforming": 2, "trend": "declining"},
    "camp_104": {"days_underperforming": 0, "trend": "improving"},
    "camp_105": {"days_underperforming": 1, "trend": "stable"},
    # camp_106 looks healthy today, but has been quietly declining for days
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