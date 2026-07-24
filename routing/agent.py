import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the API key from the .env file in the project root
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-flash-latest")

ALLOWED_LABELS = {"HEALTHY", "NEEDS_ADJUSTMENT", "CRITICAL"}


def classify_campaign(campaign: dict) -> str:
    """
    Sends campaign data to the model and asks for ONE label only.
    Returns one of: HEALTHY, NEEDS_ADJUSTMENT, CRITICAL
    """
    prompt = f"""You are classifying an ad campaign's health.
Respond with ONLY one word, no punctuation, no explanation.
Choose exactly one label from this set: HEALTHY, NEEDS_ADJUSTMENT, CRITICAL

Campaign data:
- daily_spend: {campaign['daily_spend']}
- budget_remaining: {campaign['budget_remaining']}
- clicks: {campaign['clicks']}
- impressions: {campaign['impressions']}
- conversions: {campaign['conversions']}
- ctr: {campaign['ctr']}%
- cost_per_conversion: {campaign['cost_per_conversion']}

Label:"""

    response = model.generate_content(prompt)
    label = response.text.strip().upper()

    # Safety check: if the model returns something unexpected, fail safely
    if label not in ALLOWED_LABELS:
        return "CRITICAL"  # fail safe: escalate rather than guess

    return label


def run_workflow(campaign: dict) -> dict:
    """
    Ordinary, testable code. No model call here — just fixed logic
    based on the label the classifier returned.
    """
    label = classify_campaign(campaign)

    if label == "HEALTHY":
        return {"action": "KEEP_RUNNING", "label": label}
    elif label == "NEEDS_ADJUSTMENT":
        return {"action": "REDUCE_BUDGET", "label": label}
    else:  # CRITICAL
        return {"action": "PAUSE_CAMPAIGN", "label": label}


# ---- Test cases (same ones used in the Reactive agent) ----
if __name__ == "__main__":
    test_campaigns = [
        {
            "campaign_id": "camp_101",
            "daily_spend": 250, "budget_remaining": 3000,
            "clicks": 120, "impressions": 15000,
            "conversions": 0, "ctr": 0.8, "cost_per_conversion": 0
        },
        {
            "campaign_id": "camp_102",
            "daily_spend": 150, "budget_remaining": 3000,
            "clicks": 60, "impressions": 20000,
            "conversions": 5, "ctr": 0.3, "cost_per_conversion": 30
        },
        {
            "campaign_id": "camp_103",
            "daily_spend": 100, "budget_remaining": 80,
            "clicks": 200, "impressions": 10000,
            "conversions": 10, "ctr": 2.0, "cost_per_conversion": 10
        },
        {
            "campaign_id": "camp_104",
            "daily_spend": 100, "budget_remaining": 2000,
            "clicks": 300, "impressions": 10000,
            "conversions": 15, "ctr": 3.0, "cost_per_conversion": 6.6
        },
        {
            "campaign_id": "camp_105",
            "daily_spend": 400, "budget_remaining": 2500,
            "clicks": 500, "impressions": 20000,
            "conversions": 2, "ctr": 2.5, "cost_per_conversion": 200
        },
    ]

    for campaign in test_campaigns:
        result = run_workflow(campaign)
        print(f"Campaign: {campaign['campaign_id']}")
        print(f"  Model label: {result['label']}")
        print(f"  Decision:    {result['action']}")
        print()