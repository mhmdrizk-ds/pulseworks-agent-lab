# Pulseworks Agent Lab — Presentation Slide Content
**For building the deck in Canva. Each `---` is a new slide. Speaker notes are in *italics* under each slide — say them, don't put them on the slide itself.**

---

## SLIDE 1 — Title
**Pulseworks Agent Lab**
Four ways to decide what happens next to a campaign

*Team 3 — Pulseworks Marketing B*

---

## SLIDE 2 — The Setup
**We're account managers at Pulseworks.**

Every morning, before anything else:
- Open the dashboard
- Go client by client, campaign by campaign
- Decide: leave it running, tweak something, pause it, or flag it for a manager

*"That was fine when we had a handful of active campaigns. It stopped being fine as the client roster grew."*

---

## SLIDE 3 — What Was Going Wrong
- Missing early warning signs — a campaign that looked fine today but had been sliding for over a week
- Campaigns burning through budget faster than anyone noticed
- Five minutes per decision × fifty campaigns × every single morning

*"We needed something that could make the first pass for us."*

---

## SLIDE 4 — The First Attempt: Reactive Agent
**A pure rule-based agent. No model call at all.**

- Zero conversions + ROAS under 1 → `PAUSE_CAMPAIGN`
- High audience fatigue → `CHANGE_AUDIENCE`
- Low CTR → `REFRESH_CREATIVE`

Cheap. Instant. Free.

*"And it actually worked — for the obvious cases."*

---

## SLIDE 5 — Where the Reactive Agent Broke
**camp_107: looks healthy today. CTR good. Conversion rate good. ROAS solid.**

The rules say: `CONTINUE`

What the rules can't see: **8 straight days of decline.**

*"It's about to fall off a cliff, and our reactive agent has no idea, because the rules only look at what's true right now."*

---

## SLIDE 6 — Reaching for the Model: Routing Agent
**One constrained model call classifies the campaign; fixed code acts on the label.**

Still one API call. Still one clean flow. Judgment instead of if/else.

*"It's not locked into a rigid priority order — it can weigh conflicting signals more like a person would."*

---

## SLIDE 7 — New Problems, Not Just New Wins
- A free-tier "latest" model alias silently resolved to a preview model with a **20-requests-per-day cap** — we didn't even choose that on purpose
- Burned through it in one test run; had to switch to a pinned stable model plus retry/backoff logic

*"That's a class of problem a rule-based agent never has."*

---

## SLIDE 8 — The Moment That Surprised Us
**Same exact input. Zero conversions. ROAS 0.4. About as unambiguous as it gets.**

| | Decision |
|---|---|
| Reactive agent | `PAUSE_CAMPAIGN` ✅ |
| Routing agent | `REFRESH_CREATIVE` ❌ |

*"That's not a hypothetical failure mode. That's something we watched happen."*

---

## SLIDE 9 — Going Further: The Unconstrained ReAct Agent
**We gave the model full freedom: pick its own tools, decide its own stopping point.**

Tools available: check history, check creative, check audience fatigue, then choose one of seven actions.

No schema. No allow-list. No step limit — just a generous safety leash so a broken run can't hang forever.

*"We wanted to see what the model would do with genuine freedom, including checking nothing at all if it felt confident."*

---

## SLIDE 10 — It Found What the First Two Missed
**We ran camp_107 through it — the campaign hiding 8 days of decline.**

Without being told hidden data existed by name, the agent chose to call `get_campaign_history` on its own — and in one run, correctly flagged the contradiction:

*"The campaign is on a strong downward trend and has underperformed for over a week despite reports of good creative and low audience fatigue... This discrepancy suggests an underlying issue that requires a human manager to investigate."*
→ **`escalate_to_manager`**

---

## SLIDE 11 — But Freedom Has a Cost: Non-Determinism
**We ran the exact same campaign (camp_107) twice.**

| Run | Calls made | Checked | Final decision |
|---|---|---|---|
| Run A | 2 | History only | `change_audience` |
| Run B | 4 | History, creative, fatigue | `escalate_to_manager` |

*"Same input. Same code. Two different investigations, two different answers. Reactive can't vary at all. Routing varies far less. This is a real, observed cost of giving the model full control over when it stops."*

---

## SLIDE 12 — The Operational Cost
- Mid-project: the SDK we built against (`google-generativeai`) was fully deprecated by Google
- Mid-project: the model we'd chosen (`gemini-2.5-flash`) was retired for new users entirely — not a quota issue, a hard removal
- Landed on `gemini-3-flash-preview` — free tier, but only **20 requests per day**
- A single campaign can cost 2–4 calls → caps us at roughly one full 10-campaign test run per day

*"A rule-based agent is simply immune to an entire category of failure we hit three separate times."*

---

## SLIDE 13 — Finding the Right Amount of Control
[**Bring up the full comparison table here — see Slide 14.**]

- Pure rules: fast, free, predictable — but blind to anything outside today's snapshot, and rigid about priority order
- Free-roaming model: more flexible, catches what rules miss — but can misjudge even the clearest cases, and comes with real operational cost: rate limits, quota caps, non-determinism

*"Neither extreme was right on its own."*

---

## SLIDE 14 — Comparison Table
*(Insert your actual table here — pull current numbers from the README. As of now:)*

| | Reactive | Routing | Unconstrained ReAct | Constrained ReAct |
|---|---|---|---|---|
| Model calls per request | 0 | 1 | ~2–4 (varies by run) | *(in progress)* |
| Cost | Free | ~Free | Free tier, hard daily cap | *(in progress)* |
| Latency | Instant | ~1–2s | ~13–50s (pacing-dominated) | *(in progress)* |
| Uses hidden history? | No | No | Yes, every observed run | *(in progress)* |
| What broke | Blind to history/trend | Wrong call on obvious case | Non-deterministic decisions | *(in progress)* |

---

## SLIDE 15 — Live Demo
**[Switch to live demo or play recording here]**

Show: `camp_107` running through the unconstrained agent — watch it choose to check history unprompted, and land on its final decision.

*Recording strongly recommended over live, given the 20-requests-per-day quota — you do not want to burn real quota, or hit a wall, mid-presentation.*

---

## SLIDE 16 — Where It Stands Now: What We'd Still Worry About
- The free-tier quota ceiling means neither Routing nor Unconstrained ReAct is viable at real volume — a paid tier or different provider would be needed before this touches a real client account
- Reactive's fixed priority order means a campaign with multiple problems firing at once only ever gets the first-matched action, not necessarily the most urgent one
- Unconstrained ReAct's non-determinism is a real risk for a system recommending changes to real client budgets and targeting — the same input shouldn't produce different advice depending on the run

---

## SLIDE 17 — What We'd Try Next
- Give the constrained ReAct agent's history-lookup behavior real test coverage — does forcing a schema, an allow-list, and a MAX_STEPS budget keep the reliability of routing *and* the hidden-history catch of ReAct?
- Consider whether routing + a lightweight, always-on history check gets most of ReAct's benefit without its operational cost
- If this goes to production: budget for a paid API tier from day one — the free tier was never going to survive real volume

*"camp_107 is exactly the test case we'd point to first — it's the one no architecture handled the same way twice."*

---

## SLIDE 18 — Thank You / Questions
**Pulseworks Agent Lab**
Team 3 — Pulseworks Marketing B

*(Repo link / contact info as needed)*
