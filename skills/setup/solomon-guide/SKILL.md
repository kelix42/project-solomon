---
name: solomon-guide
phase: decision
description: Complete reference guide for the Solomon system — what it is, how it works, all skills, commands, and how to maintain it. Load this when onboarding a new user or when someone needs to understand the full system.
version: 0.1.0
author: Lynx + Sunny---

# Solomon — System Guide

This is the living reference document for the Solomon system. It explains what Solomon is, how it works, and how to use it. Update this guide whenever new skills, commands, or capabilities are added.

---

## What is Solomon?

Solomon is a personal business brain built on top of the Hermes agent. It learns how a business owner thinks — their beliefs, principles, hard limits, goals, and vocabulary — and gradually takes over the decisions and tasks that don't need the owner's direct attention.

The vision: by spending 30 days feeding Solomon your thinking, you get an agent that handles 80% of your decisions via simple one-tap approvals or autonomously — freeing you to focus on the work only you can do.

---

## How it works

Solomon has four layers:

1. Profile — the foundation
   Seven onboarding sessions build a YAML file for each area of the owner's thinking. These live at /opt/data/solomon/profile/ and are updated over time as Solomon learns more.

2. Listening loop — the ongoing input
   Every voice recording the owner makes (via Plaud or any recorder) gets forwarded by email. Solomon processes each transcript in three passes: summarize, extract learnings, propose actions.

3. Decision log — the training signal
   Every decision Solomon proposes and the owner's response gets logged at /opt/data/solomon/decisions/decision-log.yaml. Approvals, edits, and rejections all teach Solomon something.

4. Mentoring sessions — the recalibration loop
   Periodic structured reviews between Solomon and the owner. Covers recent decisions, surfaces patterns, corrects misalignments, and updates the profile. Run weekly or whenever Solomon feels off.

5. Memory — the fast-access layer
   Only the highest-signal facts go here — non-negotiables, core goals, critical rules. Always active, always present. Kept lean intentionally. Full detail lives in YAML files.

---

## Onboarding sessions

Complete these in order. Each is a conversational interview.

Session 0: Industry & Sector — what world the brain operates in
Session 1: Belief System — core assumptions about business, money, people, risk
Session 2: Why — motivations and ultimate goals
Session 3: Principles — operating rules and decision logic
Session 4: Ideal Outcomes — what the best version of the business looks like
Session 5: Non-Negotiables — hard limits that never get crossed
Session 6: Taxonomy — shared vocabulary, categories, and key metrics

---

## Commands

"onboarding status" — shows a checklist of completed and pending sessions
"start session 0" through "start session 6" — begins or resumes a specific session
"solomon status" — same as onboarding status

---

## Skills reference

solomon-setup — run once on a fresh Hermes instance to initialize Solomon
solomon-guide — this document
solomon-onboarding-status — powers the "onboarding status" command
solomon-onboarding-00-industry — Session 0 interview
solomon-onboarding-01-belief-system — Session 1 interview
solomon-onboarding-02-why — Session 2 interview
solomon-onboarding-03-principles — Session 3 interview
solomon-onboarding-04-ideal-outcomes — Session 4 interview
solomon-onboarding-05-non-negotiables — Session 5 interview
solomon-onboarding-06-taxonomy — Session 6 interview
solomon-profile — master profile loader, load at start of any serious session
solomon-listening-agent — processes incoming Plaud transcripts
solomon-decision-log — logs a proposed decision and the owner's response
solomon-mentoring-session — runs a periodic review and recalibration session

---

## Profile files

All profile files live at /opt/data/solomon/profile/

00-industry.yaml
01-belief-system.yaml
02-why.yaml
03-principles.yaml
04-ideal-outcomes.yaml
05-non-negotiables.yaml
06-taxonomy.yaml

## Decision log

/opt/data/solomon/decisions/decision-log.yaml

Every proposed decision and owner response. Never modified, only appended. Reviewed during mentoring sessions.

## Mentoring sessions

/opt/data/solomon/mentoring/YYYY-MM-DD-mentoring.yaml

One file per session. Captures decisions reviewed, patterns identified, profile updates made, and calibration score.

Each file has a last_updated field. They are living documents — never delete old entries, move them to a corrected section with a date.

---

## Input pipeline

Current input: Plaud voice recorder → AutoFlow → email → Hermes agent
Processing skill: solomon-listening-agent
Delivery: Telegram (the owner's chat)

---

## Design principles

- Generic by default — no owner-specific details hardcoded into skills
- One question at a time during interviews
- Never propose anything that conflicts with non-negotiables
- Propose, don't act — owner always makes the final call
- Living documents — profile files and skills get updated as understanding deepens
- Silence is worse than a false positive — when in doubt, surface it

---

## Changelog

v0.1.0 — Initial build. 7 onboarding skills, master profile skill, setup skill, status skill, listening agent skill. Folder structure initialized.
v0.2.0 — Added decision log, mentoring session skill, and mentoring/decisions folder structure. Learning loop is now complete.
