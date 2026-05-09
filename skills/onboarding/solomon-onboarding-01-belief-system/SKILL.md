---
name: solomon-onboarding-01-belief-system
phase: interview
description: Solomon onboarding session 1 — Belief System. Interviews the owner about their core beliefs about business, money, people, and risk. Requires session 0 to be complete first.
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding — Session 1: Belief System

This session captures the owner's core beliefs — the deep assumptions they hold about how the world works, how business works, how people behave, and what money means. These beliefs are the invisible layer beneath every decision.

## Prerequisites

Session 0 (Industry & Sector) must be complete. Load /opt/data/solomon/profile/00-industry.yaml for context before starting.

## Your role

Conduct a focused interview. One question at a time. Probe where answers are shallow. The goal is to surface beliefs the owner holds strongly enough that they would act on them even under pressure.

## Questions to cover

1. What do you believe about how money works — how it's made, kept, and lost?
2. What do you believe about people — employees, partners, customers? Are people generally trustworthy or do they need to be managed carefully?
3. What do you believe about risk? Is it something to minimize, embrace, or price correctly?
4. What do you believe about debt and leverage?
5. What do you believe separates successful people in your industry from unsuccessful ones?
6. What do you believe about competition — do you engage with it, ignore it, or avoid it?
7. What do you believe about growth — fast and aggressive or slow and controlled?
8. Is there anything you believe about business that most people in your world would disagree with?
9. What have you been proven wrong about — a belief you held that reality corrected?

## When the interview is complete

Produce a file at /opt/data/solomon/profile/01-belief-system.yaml:

```yaml
last_updated: <date>
beliefs:
  money: <their belief about money>
  people: <their belief about people>
  risk: <their belief about risk>
  debt_leverage: <their belief about debt and leverage>
  success_factors: <what separates winners from losers in their world>
  competition: <their stance on competition>
  growth: <their philosophy on growth pace>
contrarian_beliefs:
  - <beliefs they hold that others would disagree with>
corrected_beliefs:
  - <beliefs they used to hold that reality proved wrong>
raw_notes: <anything important that didn't fit above>
```

After writing the file, save any strong or contrarian beliefs to memory using the memory tool. Prefix with [solomon-profile].

Tell the owner session 1 is complete and the next session is Session 2 — Why.

## Rules

- One question at a time.
- The corrected beliefs question is important — it reveals intellectual honesty and how they update.
- Don't push back on beliefs. Capture them accurately even if they seem unconventional.
- If a belief seems surface-level ("I believe in working hard"), probe for the underlying assumption.
