# ELIZA Listening — interview-phase only

Solomon is **not** a chatbot. It borrows ELIZA's interview *technique* (`archives/eliza-source-MAD-SLIP.txt` for original) and applies it ONLY in the interview phase (onboarding, mentoring, level-up). Decision phase does not reflect.

## What we borrow

- **Reflective interviewer style.** Mirror, probe, draw the owner out.
- **Keyword-triggered probing.** Each domain has a ranked probe library (`skills/interview/solomon-interview-engine/probe_library/`).
- **Reflection through exact-word echoing.** Reuse the owner's verbatim phrases. If they say "we never nickel-and-dime customers," the probe is "When has nickel-and-diming a customer been tempting?" — never paraphrased.
- **Decomposition.** Turn one vague answer into multiple targeted probes.
- **Ranked fallbacks.** When a keyword runs dry, jump to a related one or use a generic forward prompt.
- **Priority ranking.** Some keywords matter more than others for cloning judgment. Lower priority number wins.

## What we ignore

- Canned non-answers ("HMMM", "I SEE"). Replaced with extraction-forcing fallbacks that still capture data.
- Runtime script editing. The probe library is read-only at runtime; updates ship as new versions of the skill.

## What we add

- **Concrete-example forcing**: always push from principle to last real instance.
- **Contradiction detection**: real-time via `solomon-contradiction-check` writing to `db.clarification_queue`.
- **Coverage tracking**: `db.coverage` tells the engine which sub-topics are still thin.
- **Confidence scoring**: stated / repeated / exemplified.
- **Vocabulary capture**: `solomon-vocabulary-capture` builds `db.vocabulary` from every owner answer.

## Invocation rule

If the loaded skill carries `phase: interview`, the ELIZA rule applies. Otherwise it does not. Decision-phase skills load the populated profile and act decisively.
