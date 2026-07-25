# Pulseworks Agent Lab

**Team 3 — Pulseworks Marketing B**

## The Company

Pulseworks is a digital marketing agency that runs paid ad campaigns (Facebook and
Google Ads) on behalf of multiple clients at once. Every campaign reports live
performance metrics — CTR, conversion rate, ROAS, daily spend, remaining budget,
audience fatigue, and creative performance — and someone has to decide, campaign
by campaign, what happens next: keep it running, adjust something (creative,
audience, budget), pause it, or escalate it to a human manager.

## The Problem

Account managers at Pulseworks were reviewing campaign dashboards manually every
morning, campaign by campaign, client by client. This worked when the agency had
a handful of active campaigns. It stopped working as the client roster grew:
managers were missing early warning signs (a campaign that looks fine today but
has been quietly declining for a week), reacting too slowly to campaigns burning
through budget, and spending hours a day on a decision that mostly followed
recognizable patterns.

We built and compared four different agent architectures that all solve the same
problem — given a campaign's current metrics, decide the right action — to feel,
in our own code, how each one behaves differently when it hits the same input.

**Why this needs an agent, not a simple script:** the "right" action depends on
more than one metric at once (a good CTR can hide a bad ROAS; a healthy-looking
day can hide a week of decline visible only in campaign history), and the
weighting between those signals isn't a fixed formula — it's closer to judgment
than arithmetic. That's exactly the kind of decision where the four
architectures are expected to diverge.

## The Four Architectures

| Folder | Architecture | Status |
|---|---|---|
| `reactive/` | Rule-based if/then logic, no model call | ✅ Done |
| `routing/` | Single constrained model call classifies into a fixed label, then fixed code acts on it | ✅ Done |
| `unconstrained_react/` | Free-form ReAct loop — model chooses its own tools and stopping point | 🚧 Loop built, testing across all 10 campaigns |
| `constrained_react/` | Same reasoning loop, but schema-validated steps, a tool allow-list, and a MAX_STEPS budget | ⬜ Not started |

All four agents are evaluated against the same 10 test campaigns in
`shared/test_cases.py`, so the comparison below is apples-to-apples.

## Repo Structure

```
pulseworks-agent-lab/
├── .env                          # API keys — never committed
├── .gitignore
├── README.md
│
├── shared/
│   ├── data.py
│   ├── tools.py
│   └── test_cases.py
│
├── reactive/
│   └── agent.py
│
├── routing/
│   └── agent.py
│
├── unconstrained_react/
│   ├── agent.py                  # the ReAct loop
│   ├── prompts.py                # SYSTEM_PROMPT
│   └── model_client.py           # Gemini API wrapper (google-genai)
│
└── constrained_react/
    ├── agent.py                  # not started yet
    ├── schema.py
    └── tool_allowlist.py
```

## Shared Code

- `shared/data.py` — the 10 test campaigns (visible fields) plus a hidden
  `_HISTORY` table (days underperforming, trend) accessible only through
  `get_campaign_history()`. Reactive and Routing never call this function;
  only the ReAct agents are meant to reach for it through a tool.
- `shared/tools.py` — the action functions shared by all four agents
  (`pause_campaign`, `refresh_creative`, `decrease_budget`, `increase_budget`,
  `change_audience`, `escalate_to_manager`, `continue_campaign`) plus the
  information tools used only by the ReAct agents
  (`get_campaign_history`, `check_creative_performance`,
  `check_audience_fatigue`), registered in `TOOLS` for allow-listing.
- `shared/test_cases.py` — imports `CAMPAIGNS` from `data.py` so every agent
  runs against the exact same 10 inputs.

## How to Run

Each agent is runnable on its own from the project root:

```bash
pip install google-genai python-dotenv tenacity
python reactive/agent.py
python routing/agent.py
```

`routing/agent.py` and `unconstrained_react/agent.py` both call the Gemini
API and share a single `.env` file in the project root:

```
GOOGLE_API_KEY=your_key_here
```

Get a free key at [Google AI Studio](https://aistudio.google.com).

**Note on package/model versions:** both agents use the current
[`google-genai`](https://pypi.org/project/google-genai/) package
(`from google import genai`, `genai.Client(...)`), **not** the older
`google-generativeai` package — that package is now deprecated by Google and
should not be installed. We also moved off `gemini-2.5-flash` after it was
fully retired for new users mid-project (a hard removal, not a quota issue),
and off the floating alias `gemini-flash-latest` after it silently resolved
to a low-quota preview model. Both agents currently run against
`gemini-3-flash-preview`. Model availability on Google's side has moved fast
enough during this project that it's worth checking
[the current model list](https://ai.google.dev/gemini-api/docs/pricing)
before assuming either agent's model string still exists.

Both scripts pace requests (13s apart) and retry automatically on transient
errors, but fail fast (no wasted retries) on a 429 quota error. The free
tier's quota has two independent dimensions worth knowing about:
- **Per-minute rate limit** — recoverable by waiting and retrying, handled
  automatically.
- **Daily quota** — for `gemini-3-flash-preview` specifically, this is
  **20 requests/day**, which is a hard stop, not something retrying fixes.
  Since a single unconstrained-agent campaign can cost 2-4 model calls, this
  caps a full 10-campaign run at roughly one clean run per day. If you hit
  this, the error message will say so explicitly — wait for the daily reset
  or switch to a different free-tier model.

`unconstrained_react/agent.py` also saves its results incrementally to
`unconstrained_react/results.json` after every campaign (not just at the
end), so a quota error partway through a run doesn't lose progress already
made — just re-run the script later to pick up where it left off (this
overwrites `results.json`, so back up the file first if you want to keep an
earlier partial run for comparison).

There is no MAX_STEPS in `unconstrained_react/` — only a generous safety
ceiling of 20 loop iterations purely to stop a broken run from hanging
forever. It is not meant to be hit under normal behavior; if it ever is,
that's a failure worth noting, not a design feature.

*(Run instructions for `constrained_react/` — TBD, not started yet.)*

## Comparison Table

| | Reactive | Routing | Unconstrained ReAct | Constrained ReAct |
|---|---|---|---|---|
| Model calls per request | 0 | 1 | ~2-4 (varies by campaign and by run — see notes) | TBD |
| Cost | Free | ~Free (Gemini free tier) | Free tier, but daily quota is a hard constraint (see below) | TBD |
| Latency | Instant | ~1-2s per call | ~13-50s per campaign (rate-limit pacing dominates, not model latency) | TBD |
| Uses hidden history? | No (can't) | No (can't) | Yes — checked `get_campaign_history` in every observed run so far | TBD |

**What broke, in our own test cases:**

- **Reactive:** correctly flags the obviously bad campaign (camp_108: no
  conversions, ROAS 0.4 → `PAUSE_CAMPAIGN`) because it matches the rule exactly.
  But it can't see campaign history at all, so a campaign that looks fine today
  but has been declining for 8 days (camp_107) sails through as `CONTINUE`.
  It also can't weigh conflicting signals — priority order is fixed, so a
  campaign with high audience fatigue *and* a critical ROAS gets whatever rule
  comes first in the if/else chain, not necessarily the most urgent one.

- **Routing:** on the *same* obviously-bad campaign (camp_108) that Reactive
  correctly paused, the model instead returned `REFRESH_CREATIVE` — a real,
  observed inconsistency between the two architectures on identical input, not
  a hypothetical. It also can't access hidden history (same blind spot as
  Reactive, since the classification prompt only sees today's snapshot), and it
  introduced a new failure mode Reactive doesn't have: free-tier rate limits.
  The first model we tried (`gemini-flash-latest`, a floating alias) resolved
  to a preview model with a 20-requests-per-day cap; switching to the stable
  `gemini-2.5-flash` and adding retry/backoff plus request pacing fixed it, but
  it's a new class of problem a rule-based agent never has.

- **Unconstrained ReAct:** the system prompt deliberately gives no strict
  output format — the model is only told to write `ACTION: tool_name` and
  `FINAL ANSWER: tool_name` as a suggestion, not a schema. In practice, the
  regex-based parser (`parse_action` / `parse_final_answer` in `agent.py`)
  caught the model's phrasing correctly in every observed run — no unparsed
  or hallucinated-tool-name turns yet, though we haven't run enough volume
  to call that reliable. Two findings stood out as more significant:

  - **Non-determinism on identical input.** Running `camp_107` (a campaign
    that looks healthy on the surface but has been declining for 8 days per
    its hidden history) twice, on the same code, produced two different
    outcomes: one run made 2 model calls and returned `change_audience`
    without checking creative or fatigue; another made 4 calls, checked
    history, creative, *and* fatigue, and returned `escalate_to_manager`
    with reasoning that explicitly named the contradiction between healthy
    surface metrics and a declining trend. Reactive can't vary at all;
    Routing varies far less, since it's one constrained classification
    call. This variability — both in the final decision and in how
    thoroughly the agent investigates — is a direct, observed cost of
    giving the model full freedom over its own stopping point.
  - **It reliably chose to check hidden history on its own.** In every
    completed run so far, the agent called `get_campaign_history` before
    deciding, even though nothing in the prompt told it that field existed
    by name — it inferred there might be more to check. This is the
    capability Reactive and Routing structurally lack.

  A third, more operational finding: the free tier for `gemini-3-flash-preview`
  has a **daily** quota of only 20 requests, not just a per-minute rate
  limit. Since a single campaign can cost 2-4 calls, this caps a full run at
  roughly 5-8 campaigns per day — nowhere near enough to comfortably test
  10 campaigns multiple times in one session. This is a real, quantified
  cost of the ReAct approach that Reactive (0 calls) will never hit and
  Routing (1 call per campaign, so ~20 campaigns/day) hits far less often.
  We also hit a mid-project SDK deprecation (`google-generativeai` →
  `google-genai`) and a fully retired model (`gemini-2.5-flash` no longer
  available to new users at all) — a class of failure a rule-based agent
  is simply immune to.

  Full 10-campaign comparison numbers — TBD, pending a clean run once the
  daily quota resets.

*(Constrained ReAct section — TBD, not started. Expect: does it catch the same
camp_107 case while staying inside MAX_STEPS? Does schema validation reject
malformed steps that the unconstrained version would have silently
mishandled? Does constraining the loop reduce the non-determinism observed
above, or just make the *format* more predictable while the underlying
decision still varies?)*

## What We'd Still Worry About in Production

*(To be finalized closer to the presentation — draft points:)*
- Routing's free-tier quota limits are not production-viable as-is; would need
  a paid tier or a different provider.
- Reactive's fixed priority order is brittle — a campaign with multiple issues
  firing at once only ever gets the first-matched action, not necessarily the
  most urgent one.
- Neither Reactive nor Routing can see campaign history, which is exactly the
  kind of signal that matters most for genuinely proactive account management.
- Unconstrained ReAct's free-tier daily quota (20 requests/day for
  `gemini-3-flash-preview`) is not remotely production-viable for an agency
  managing many client campaigns daily — a paid tier or a different provider
  would be required before this could run unattended.
- Unconstrained ReAct produced different final decisions on the same input
  across different runs (see camp_107 above). For a system recommending
  budget or targeting changes to real client campaigns, that unpredictability
  is a real risk — it's part of why we expect the constrained version to
  matter, not just as an academic exercise.