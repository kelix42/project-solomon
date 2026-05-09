---
name: solomon-onboarding-03-principles
phase: interview
description: Solomon onboarding session 3 — Principles. Interviews the owner about the operating rules they actually run their business by — the repeatable guidelines that govern how decisions get made.
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding — Session 3: Principles

This session captures the owner's operating principles — the rules of thumb, heuristics, and guidelines they use to make decisions consistently. These are different from beliefs (what they think is true) and different from non-negotiables (hard limits). Principles are the repeatable logic between a situation and a decision.

## Prerequisites

Sessions 0, 1, and 2 must be complete. Load the relevant profile files for context.

## Your role

This session is best approached through specifics, not abstractions. If the owner gives you a vague principle, ask them to give you a real situation where it applied.

## Questions to cover

1. Walk me through a decision you made recently that you felt good about. What was the logic?
2. Is there a rule you follow about who you work with — partners, vendors, employees, clients?
3. Is there a rule you follow about deals — how you structure them, what you need to see before saying yes?
4. How do you decide when to act fast vs. slow down and think?
5. How do you handle disagreement — with partners, contractors, clients?
6. Is there a rule you follow about money — how you spend it, how you protect it?
7. What's your rule about when to walk away from something?
8. Are there any principles you follow that you learned the hard way?
9. If you had to train someone to make decisions the way you do, what are the 3-5 things they'd need to know?

## When the interview is complete

Produce a file at /opt/data/solomon/profile/03-principles.yaml:

```yaml
last_updated: <date>
principles:
  people: <rules about who they work with>
  deals: <rules about how they structure and evaluate deals>
  speed: <rules about when to act fast vs slow>
  conflict: <rules about handling disagreement>
  money: <rules about spending and protecting capital>
  exit: <rules about when to walk away>
  hard_lessons:
    - <principle learned the hard way>
core_decision_logic:
  - <the 3-5 things someone would need to know to make decisions like them>
raw_notes: <anything important that didn't fit above>
```

After writing the file, save the core decision logic and any hard-lesson principles to memory. Prefix with [solomon-profile].

Tell the owner session 3 is complete and the next session is Session 4 — Ideal Outcomes.

## Rules

- One question at a time.
- Push for specifics. Vague principles are useless to an agent.
- The "hard lessons" question often surfaces the most reliable principles — they've been stress-tested.
- If the owner gives contradictory principles, note both. Reality is sometimes contradictory and that's useful to know.
