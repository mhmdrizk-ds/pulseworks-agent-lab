"""
Shared action functions used by the Reactive and Routing agents.
Each function takes a campaign dict and returns a decision dict
with 'action' and 'reason' keys.
"""
def pause_campaign(campaign: dict) -> dict:
    return {
        "action": "PAUSE_CAMPAIGN",
        "reason": f"No conversions and ROAS below 1 ({campaign['roas']})."
    }
def refresh_creative(campaign: dict) -> dict:
    return {
        "action": "REFRESH_CREATIVE",
        "reason": f"CTR is low ({campaign['ctr']}%), creative may be fatigued."
    }
def decrease_budget(campaign: dict) -> dict:
    return {
        "action": "DECREASE_BUDGET",
        "reason": f"ROAS below 1.5 ({campaign['roas']}), reducing spend."
    }
def change_audience(campaign: dict) -> dict:
    return {
        "action": "CHANGE_AUDIENCE",
        "reason": "Audience fatigue is High, targeting needs to change."
    }
def escalate_to_manager(campaign: dict) -> dict:
    return {
        "action": "ESCALATE_TO_MANAGER",
        "reason": f"Only {campaign['remaining_budget']} left in budget."
    }
def continue_campaign(campaign: dict) -> dict:
    return {
        "action": "CONTINUE_CAMPAIGN",
        "reason": "Campaign performance is within acceptable range."
    }