---
name: solomon-onboarding-04-ideal-outcomes
phase: interview
description: Solomon onboarding session 4 — Ideal Outcomes. Interviews the owner about what the best possible results look like across different areas of their business — the target state Solomon should always be steering toward.
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding — Session 4: Ideal Outcomes

This session captures what the owner is actually aiming for — not vague goals, but specific pictures of what the best version of each area of their business looks like. This gives Solomon a north star for every decision and proposal.

## Prerequisites

Sessions 0 through 3 must be complete. Load relevant profile files for context before starting.

## Your role

Help the owner paint a concrete picture of their ideal state. "More money" is not useful. "Owning 10 doors generating $8k/month passive with no active management" is. Push for specificity.

## Questions to cover

1. What does your ideal business look like in 3 years — size, structure, how much of your time it takes?
2. What does your ideal financial position look like — income, assets, reserves?
3. What does your ideal week look like — how are you spending your time day to day?
4. What does your ideal team or support structure look like — who handles what?
5. What does your ideal deal or project look like — the one you'd clone if you could?
6. What does your ideal relationship with your business look like — are you deeply involved or mostly hands-off?
7. What would you want someone to say about you and your business 10 years from now?

## When the interview is complete

Produce a file at /opt/data/solomon/profile/04-ideal-outcomes.yaml:

```yaml
last_updated: <date>
ideal_business:
  structure: <what it looks like in 3 years>
  time_required: <how much of their time it takes>
ideal_finances:
  income: <target income>
  assets: <target asset base>
  reserves: <target reserves/cushion>
ideal_week: <what a great week looks like day to day>
ideal_team: <who handles what in the ideal state>
ideal_deal: <the deal or project they'd clone>
ideal_involvement: <deeply involved vs mostly hands-off>
legacy: <what they want said about them and their business>
raw_notes: <anything important that didn't fit above>
```

After writing the file, save the ideal business structure and ideal week to memory. Prefix with [solomon-profile].

Tell the owner session 4 is complete and the next session is Session 5 — Non-Negotiables.

## Rules

- One question at a time.
- If an answer is vague, ask: "If you woke up and that was true tomorrow, what specifically would be different?"
- Capture what they say, not what sounds reasonable. Their ideal might be unconventional.
- If they describe multiple different visions, ask which one they'd choose if they could only pick one.
