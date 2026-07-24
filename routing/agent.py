import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Allow importing from the shared/ folder at the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.test_cases import TEST_CASES

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
- daily_spend: {campaign['spend_daily']}
- budget_remaining: {campaign['remaining_budget']}
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


# ---- Run against the shared test cases ----
if __name__ == "__main__":
    for campaign in TEST_CASES:
        result = run_workflow(campaign)
        print(f"Campaign: {campaign['id_campaign']}")
        print(f"  Model label: {result['label']}")
        print(f"  Decision:    {result['action']}")
        print()