---
name: solomon-setup
phase: decision
description: Initialize Solomon for a new user. Run this once when setting up Solomon on a fresh Hermes agent. Creates the folder structure and walks the user through what Solomon is and how to begin.
version: 0.1.0
author: Lynx + Sunny---

# Solomon — Setup

Run this skill once when a new user is setting up Solomon on their Hermes agent for the first time.

## What to do

1. Create the profile directory:
   /opt/data/solomon/profile/

2. Greet the user with this explanation (plain language, no jargon):

---

Solomon is your personal business brain, built on top of your Hermes agent.

Here is what it does:

It learns how you think — your beliefs, your principles, what you will and won't do, and what you are building toward. Over time it gets better at making decisions the way you would, so you spend less time on things that don't need you.

It has two main inputs:
- Onboarding sessions — a series of 7 interviews that build the foundation
- Your voice recordings — transcripts from your Plaud or any recording device, processed automatically when they arrive by email

Everything it learns gets saved to your profile, which lives on this machine and belongs to you.

To get started, complete the 7 onboarding sessions in order. Each one is a short interview. You can do them all at once or spread them out.

Say "onboarding status" at any time to see where you are.
Say "start session 0" to begin.

---

3. Confirm the folder was created and tell the user they are ready to begin.

## Notes for maintainers

This skill should stay generic — no names, no industries, no assumptions about the user's business. It is the entry point for any new Solomon user on any Hermes instance.

Update this skill if:
- The onboarding session list changes
- New input sources are added beyond Plaud/email
- The folder structure changes
