"""
model_client.py

Thin wrapper around the Gemini API so the agent loop stays provider-agnostic.
The loop (agent.py) only knows about call_model(conversation) -> str;
it doesn't know or care which provider is behind it.

NOTE (as of testing in July 2026): the old `google-generativeai` package is
deprecated and `gemini-2.5-flash` is no longer available to new users at
all — not a quota issue, the model itself was retired. This file uses the
new `google-genai` package and `gemini-3-flash-preview`, which currently has
a documented free tier. Model availability moves fast — if this stops
working, check https://ai.google.dev/gemini-api/docs/pricing for the
current free-tier model list before assuming the code is broken.
"""

import os
import time
from google import genai
from google.genai.errors import ClientError
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

MODEL_NAME = "gemini-3-flash-preview"

# Free-tier pacing: space requests out so we don't trip per-minute limits.
# The unconstrained loop can make several calls per campaign, so this adds
# up fast across 10 test campaigns — budget for it.
SECONDS_BETWEEN_REQUESTS = 13
_last_call_time = 0


def _pace_requests():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < SECONDS_BETWEEN_REQUESTS:
        time.sleep(SECONDS_BETWEEN_REQUESTS - elapsed)
    _last_call_time = time.time()


def _is_retryable(exception):
    # A 429 quota error (daily or per-minute) won't be fixed by retrying
    # a few seconds later — fail fast instead of burning more of an
    # already-exhausted daily quota on pointless retries.
    if isinstance(exception, ClientError) and exception.code == 429:
        return False
    return True


@retry(
    wait=wait_fixed(15),
    stop=stop_after_attempt(4),
    retry=retry_if_exception(_is_retryable),
)
def _call_gemini(prompt_text):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text,
    )
    return response.text


def call_model(conversation):
    """
    conversation: list of {"role": "system"/"user"/"assistant", "content": str}
    Returns: the model's reply as a plain string.

    The basic generate_content() call doesn't take a structured multi-turn
    "messages" list with roles the way Claude/OpenAI do, so we flatten the
    conversation into a single prompt, clearly labeling each turn. This is
    a simplification worth noting in your README — it's part of why token
    usage/behavior may differ slightly from a "true" multi-turn API call.
    """

    parts = []
    for turn in conversation:
        if turn["role"] == "system":
            parts.append(f"SYSTEM INSTRUCTIONS:\n{turn['content']}")
        elif turn["role"] == "user":
            parts.append(f"USER:\n{turn['content']}")
        elif turn["role"] == "assistant":
            parts.append(f"ASSISTANT (you):\n{turn['content']}")

    prompt_text = "\n\n".join(parts)

    _pace_requests()

    try:
        return _call_gemini(prompt_text)
    except ClientError as e:
        if e.code == 429:
            raise RuntimeError(
                "Hit a Gemini free-tier quota limit (429). This is often "
                "the DAILY quota, not a per-minute rate limit — preview "
                "models like gemini-3-flash-preview can have very low daily "
                "caps (as low as 20 requests/day at time of writing). "
                "Check current limits at "
                "https://ai.google.dev/gemini-api/docs/rate-limits, or wait "
                "for the daily reset. Original error: " + str(e)
            )
        raise