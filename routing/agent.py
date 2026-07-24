import sys
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from google.api_core.exceptions import ResourceExhausted

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

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-flash-latest")

ALLOWED_LABELS = {
    "PAUSE",
    "CHANGE_AUDIENCE",
    "REFRESH_CREATIVE",
    "DECREASE_BUDGET",
    "ESCALATE",
    "CONTINUE",
}


@retry(
    retry=retry_if_exception_type(ResourceExhausted),
    wait=wait_exponential(multiplier=2, min=15, max=60),
    stop=stop_after_attempt(5),
)
def call_model(prompt: str):
    return model.generate_content(prompt)


def classify_campaign(campaign: dict) -> str:
    prompt = f"""You are classifying an ad campaign's health and recommended action.
Respond with ONLY one label, no punctuation, no explanation.
Choose exactly one label from this set:
PAUSE, CHANGE_AUDIENCE, REFRESH_CREATIVE, DECREASE_BUDGET, ESCALATE, CONTINUE

Campaign data:
- daily_spend: {campaign['daily_spend']}
- remaining_budget: {campaign['remaining_budget']}
- ctr: {campaign['ctr']}%
- conversion_rate: {campaign['conversion_rate']}%
- roas: {campaign['roas']}
- audience_fatigue: {campaign['audience_fatigue']}
- creative_performance: {campaign['creative_performance']}

Label:"""

    response = call_model(prompt)
    label = response.text.strip().upper()

    if label not in ALLOWED_LABELS:
        return "ESCALATE"

    return label


def run_workflow(campaign: dict) -> dict:
    label = classify_campaign(campaign)

    if label == "PAUSE":
        result = pause_campaign(campaign)
    elif label == "CHANGE_AUDIENCE":
        result = change_audience(campaign)
    elif label == "REFRESH_CREATIVE":
        result = refresh_creative(campaign)
    elif label == "DECREASE_BUDGET":
        result = decrease_budget(campaign)
    elif label == "ESCALATE":
        result = escalate_to_manager(campaign)
    else:
        result = continue_campaign(campaign)

    result["label"] = label
    return result


def main():
    print("=" * 70)
    print("Deterministic Routing Marketing Agent")
    print("=" * 70)

    for i, campaign in enumerate(TEST_CASES, start=1):
        result = run_workflow(campaign)

        print(f"\nCampaign {i}")
        print("-" * 40)

        print("Input:")
        for k, v in campaign.items():
            print(f"  {k}: {v}")

        print("\nDecision:")
        print(f"  Model label : {result['label']}")
        print(f"  Action      : {result['action']}")
        print(f"  Reason      : {result['reason']}")

        print("-" * 40)

        # Free tier is 5 requests/minute — pace requests to stay under it
        if i < len(TEST_CASES):
            time.sleep(13)


if __name__ == "__main__":
    main()