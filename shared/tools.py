def pause_campaign(campaign):
    return {
        "action": "PAUSE_CAMPAIGN",
        "reason": "Campaign has no conversions and poor ROAS."
    }


def refresh_creative(campaign):
    return {
        "action": "REFRESH_CREATIVE",
        "reason": "CTR is below acceptable threshold."
    }


def decrease_budget(campaign):
    return {
        "action": "DECREASE_BUDGET",
        "reason": "ROAS is too low."
    }


def change_audience(campaign):
    return {
        "action": "CHANGE_AUDIENCE",
        "reason": "Audience fatigue is high."
    }


def escalate_to_manager(campaign):
    return {
        "action": "ESCALATE_TO_MANAGER",
        "reason": "Remaining budget is critically low."
    }


def continue_campaign(campaign):
    return {
        "action": "CONTINUE_CAMPAIGN",
        "reason": "Campaign performance is healthy."
    }