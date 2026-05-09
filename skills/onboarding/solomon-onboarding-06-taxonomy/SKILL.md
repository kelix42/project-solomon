---
name: solomon-onboarding-06-taxonomy
phase: interview
description: Solomon onboarding session 6 — Taxonomy. Interviews the owner to build a shared vocabulary — the specific terms, categories, and classifications they use to think about their business. This is the final onboarding session.
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding — Session 6: Taxonomy

This is the final onboarding session. Its purpose is to build a shared vocabulary between the owner and Solomon — the specific words, categories, and mental models the owner uses to organize their world. Without this, Solomon might understand the intent but use the wrong language, leading to miscommunication.

## Prerequisites

Sessions 0 through 5 must be complete. Load relevant profile files for context.

## Your role

This session is more practical and less emotional than the others. Move through it at a steady pace. The goal is a clear map of how the owner categorizes their world.

## Questions to cover

1. How do you categorize your projects or deals? What buckets do they fall into?
2. How do you categorize people in your world — what types of relationships do you have and what do you call them?
3. How do you categorize your time — what kinds of work do you do and how do you think about them?
4. How do you categorize risk in your world — what does a low, medium, and high risk situation look like to you?
5. How do you categorize decisions — what makes something a small decision vs. a big one?
6. Are there any terms or phrases specific to your industry that I should know?
7. Are there any words or categories you use internally that are different from how the industry uses them?
8. How do you track and measure the health of your business — what numbers matter?

## When the interview is complete

Produce a file at /opt/data/solomon/profile/06-taxonomy.yaml:

```yaml
last_updated: <date>
project_categories:
  - <how they bucket deals/projects>
people_categories:
  - <types of relationships and what they call them>
time_categories:
  - <types of work and how they think about them>
risk_scale:
  low: <what low risk looks like>
  medium: <what medium risk looks like>
  high: <what high risk looks like>
decision_scale:
  small: <what makes a decision small>
  big: <what makes a decision big>
industry_terms:
  - term: <term>
    definition: <what it means in their context>
internal_language:
  - term: <term they use differently from industry standard>
    definition: <their specific meaning>
health_metrics:
  - <numbers they track to know the business is healthy>
raw_notes: <anything important that didn't fit above>
```

After writing the file, save key taxonomy terms to memory — especially anything that differs from standard industry usage. Prefix with [solomon-profile].

Then do the following:

1. Confirm all 7 sessions are complete (check that files 00 through 06 exist in /opt/data/solomon/profile/)
2. Tell the owner onboarding is complete
3. Load the solomon-profile skill and trigger a full profile summary
4. Tell the owner: "Solomon's foundation is set. From here, every transcript, every decision, every conversation refines it."

## Rules

- One question at a time.
- If the owner uses a term you don't recognize, ask them to define it — don't assume.
- The health metrics question is important — these become Solomon's default dashboard.
- This session closes the foundation. Make it feel like a completion, not just another form.
