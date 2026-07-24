"""
tools.py
Tools used by the ReAct agents.
"""
from shared.data import get_campaign_history as _get_campaign_history
# ==========================================================
# Information Tools
# ==========================================================
def get_campaign_history(campaign):
    """Access hidden campaign history."""
    return _get_campaign_history(campaign["campaign_id"])
def check_creative_performance(campaign):
    """Return creative performance."""
    return {
        "creative_performance": campaign["creative_performance"]
    }
def check_audience_fatigue(campaign):
    """Return audience fatigue."""
    return {
        "audience_fatigue": campaign["audience_fatigue"]
    }
# ==========================================================
# Action Tools
# ==========================================================
def pause_campaign(campaign):
    return {
        "action": "PAUSE_CAMPAIGN",
        "reason": "Campaign performance is critically poor."
    }
def change_audience(campaign):
    return {
        "action": "CHANGE_AUDIENCE",
        "reason": "Audience targeting should be updated."
    }
def refresh_creative(campaign):
    return {
        "action": "REFRESH_CREATIVE",
        "reason": "Creative assets should be refreshed."
    }
def increase_budget(campaign):
    return {
        "action": "INCREASE_BUDGET",
        "reason": "Campaign performance supports increasing the budget."
    }
def decrease_budget(campaign):
    return {
        "action": "DECREASE_BUDGET",
        "reason": "Campaign return is below expectations."
    }
def escalate_to_manager(campaign):
    return {
        "action": "ESCALATE_TO_MANAGER",
        "reason": "Remaining budget is critically low."
    }
def continue_campaign(campaign):
    return {
        "action": "CONTINUE_CAMPAIGN",
        "reason": "Campaign is performing well."
    }
# ==========================================================
# Tool Registry
# ==========================================================
TOOLS = {
    "get_campaign_history": get_campaign_history,
    "check_creative_performance": check_creative_performance,
    "check_audience_fatigue": check_audience_fatigue,
    "pause_campaign": pause_campaign,
    "change_audience": change_audience,
    "refresh_creative": refresh_creative,
    "increase_budget": increase_budget,
    "decrease_budget": decrease_budget,
    "escalate_to_manager": escalate_to_manager,
    "continue_campaign": continue_campaign,
}