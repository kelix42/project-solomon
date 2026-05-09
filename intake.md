# Solomon — Owner Intake (paste-once alternative to the 7 onboarding sessions)

This file complements the seven `solomon-onboarding-NN-*` skills. Both write to `db.captured_items` (raw rows) → derived `foundation/NN-*.yaml`. Pasted intake answers are still parsed by `solomon-extraction` + `solomon-vocabulary-capture` + `solomon-contradiction-check` (each preceded by `solomon-redact`). The only thing this file skips is the live ELIZA-style probing loop.

**How to use**: open this file, type your answers in the fenced code blocks. When you save, `solomon-onboarding` reads the file and runs the same extraction pipeline as the interactive sessions. You can run it multiple times — additional answers are appended, contradictions queue to clarification.

---

## Q0 — Voice samples (verbatim paste only; do NOT type fresh)

Paste 2–3 samples of your actual writing — emails you've already sent, Slack DMs, text messages. **Verbatim.** Don't write anything new for this; the point is to capture how you actually sound, not how you sound when you know an LLM is reading.

```
<paste verbatim>
```

⚠️ **Contamination warning**: anything you type fresh here pollutes the voice register. The `vocabulary` table builds from this section; if you write in "professional intake mode" Solomon will sound like a survey, not like you.

---

## Q1 — Industry (00-industry.yaml)

What does your business do? Who do you sell to? What's the geography? What are the 2–3 biggest risks in your sector right now? What trends matter?

```
<paste verbatim>
```

---

## Q2 — Belief system (01-belief-system.yaml)

What do you believe about: money, people, risk, debt, competition, growth? What contrarian beliefs do you hold? What did you used to believe that you've since corrected?

```
<paste verbatim>
```

---

## Q3 — Why (02-why.yaml)

What's your origin story? What's the ultimate goal? What does freedom mean to you? Who is this for? What would the finish line look like? What would failure look like? What kinds of "success" do you reject? What fuels you?

```
<paste verbatim>
```

---

## Q4 — Principles (03-principles.yaml)

Your rules for: people, deals, speed, conflict, money, exits. Hard lessons learned. What's your core decision logic when you're tired and need a fast answer?

```
<paste verbatim>
```

---

## Q5 — Ideal outcomes (04-ideal-outcomes.yaml)

In 3 years, what does the ideal business look like? Finances? Your week? Team? Last deal you closed? Your involvement level? Legacy?

```
<paste verbatim>
```

---

## Q6 — Non-negotiables (05-non-negotiables.yaml) — **most critical for safety**

What do you never do? Who do you never work with? What walk-away triggers exist? What do you refuse to compromise on? What core values are non-negotiable? What lessons made these rules? What discomfort triggers (in Solomon's behavior) should immediately escalate to you?

```
<paste verbatim>
```

⚠️ **Hard rules**: After your answers are extracted, the next mentoring session will offer to promote any rule here to a deterministic Stage-4 hard rule (with JSON-logic). Hard rules cannot be overridden by reasoning, autonomy, or owner state. Choose carefully — a hard rule that's too strict will block legitimate decisions.

---

## Q7 — Taxonomy (06-taxonomy.yaml) — final session, triggers full profile summary

Your project categories. People categories. Time categories (deep-work blocks, sacred meetings). Risk scale (1–10 — what's a 3? what's an 8?). Decision scale. Industry-specific terms. Internal language you use that an outsider wouldn't get. Health metrics you track.

```
<paste verbatim>
```

---

After you save this file, run:

```bash
hermes -s solomon-onboarding -q "ingest intake.md"
```

Solomon reads each section, runs the redaction + extraction + vocabulary + contradiction pipeline per Q, compiles `foundation/NN-*.yaml` summaries, and produces a full profile readback for your confirmation.
