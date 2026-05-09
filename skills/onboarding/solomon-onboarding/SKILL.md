---
name: solomon-onboarding
phase: interview
description: The 7-session onboarding interview flow for Solomon — builds the foundational brain profile that all future agent activity runs on. Load this skill when conducting or building any onboarding session interview for Solomon.
version: 0.1.0
author: Lynx + Sunny---

# Solomon — Onboarding System

## Purpose

Onboarding produces the foundational profile that Solomon operates from. Every decision, proposal, and action taken by Solomon should be colored by this profile. The profile is a living set of documents — refined over time as new transcripts arrive and new decisions are made.

## The 7 Sessions

Run in order. Each session is an interactive interview delivered in Telegram.

| # | Session | Output File |
|---|---------|-------------|
| 0 | Industry & Sector Context | industry_context.yaml |
| 1 | Belief System | belief_system.yaml |
| 2 | Why | why.yaml |
| 3 | Principles | principles.yaml |
| 4 | Ideal Outcomes | ideal_outcomes.yaml |
| 5 | Non-Negotiables | non_negotiables.yaml |
| 6 | Taxonomy | taxonomy.yaml |

Session 0 must come first — it provides the context that makes every other session meaningful. A belief or principle only makes sense relative to the industry and sector it applies to.

## Three-Layer Output Architecture

Every completed session produces output at three levels:

### Layer 1 — YAML Profile Files (source of truth)
- Location: /opt/data/solomon/profile/
- One file per session
- Rich, full detail
- Include a last_updated field
- These are the living documents — refined over time as transcripts teach Solomon more about the owner

### Layer 2 — solomon-profile skill
- A skill that loads and summarizes the most decision-relevant signals across all profile files
- Loaded automatically during substantive tasks so Solomon is always operating with full owner context
- Updated after each onboarding session completes and whenever a profile file is meaningfully revised

### Layer 3 — Memory entries (highest-signal facts)
- The facts that should color every single interaction (industry, core non-negotiables, etc.)
- Compressed and saved to memory so they're present before any skill is loaded
- Prefix: [solomon-profile] for easy identification

## Refinement Over Time

The listening loop (solomon-listening-agent skill) feeds back into these files. When a transcript reveals something new about how the owner operates, update the relevant YAML file — don't replace it, append or revise with evidence and update last_updated.

## Interview Conduct Rules

- One question at a time
- Plain conversational tone — no corporate language
- If the owner gives a vague answer, probe once before moving on
- After each session, read back a summary of what was captured and ask for corrections before writing the file
- Never assume — if something is ambiguous, ask

## Notes

- The solomon-profile skill does not exist yet (May 2026) — it will be created once the first onboarding session is complete
- Session 0 (industry context) is the first to be built as a skill
