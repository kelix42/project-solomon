---
name: solomon-mentoring-session
phase: interview
description: Run a periodic mentoring session between Solomon and the owner. Reviews recent decisions and transcript learnings, surfaces patterns, corrects misalignments, and refines the profile. Run weekly or whenever the owner wants to recalibrate.
version: 0.1.0
author: Lynx + Sunny---

# Solomon — Mentoring Session

A mentoring session is a structured review between Solomon and the owner. Its purpose is to close the gap between how Solomon thinks and how the owner actually thinks. Run this weekly, or any time the owner feels Solomon is drifting off course.

## Prerequisites

Load the following before starting:
- solomon-profile (full profile context)
- /opt/data/solomon/decisions/decision-log.yaml (recent decisions)
- Any recent mentoring session files from /opt/data/solomon/mentoring/

## Structure of the session

### Part 1 — Decision Review

Pull the last 7 days of entries from the decision log. For each rejected or edited decision:

- Present it to the owner: "I proposed X, you changed it to Y. Help me understand the gap."
- Listen to the explanation
- Extract the underlying principle or preference that Solomon missed
- Note whether this is a one-time exception or a pattern

For approved decisions, briefly confirm: "These felt right to you — anything worth noting about why?"

### Part 2 — Pattern Summary

After reviewing decisions, synthesize:

- Where is Solomon consistently aligned?
- Where does it keep missing? What's the pattern?
- Is there a belief, principle, or preference that isn't captured in the profile yet?

Present this summary to the owner and ask: "Does this read accurately to you?"

### Part 3 — Profile Updates

Based on the session, update the relevant profile YAML files:

- Add new principles, preferences, or rules discovered
- Correct any entries that the owner says are wrong or outdated
- Update last_updated fields
- Push any critical changes to Hermes memory

### Part 4 — Calibration Score

Ask the owner one question: "On a scale of 1-10, how well is Solomon representing your thinking right now?"

Capture the score and any comments.

## Save the session

Write a file to /opt/data/solomon/mentoring/ named by date:
YYYY-MM-DD-mentoring.yaml

```yaml
date: <date>
decisions_reviewed: <count>
approved: <count>
edited: <count>
rejected: <count>
patterns_identified:
  aligned:
    - <areas where Solomon is getting it right>
  gaps:
    - <areas where Solomon keeps missing>
new_learnings:
  - <new principles or preferences discovered>
profile_updates:
  - file: <which yaml file was updated>
    change: <what changed>
calibration_score: <1-10>
owner_comments: <verbatim if possible>
next_focus: <one thing Solomon should pay attention to before the next session>
```

## Closing the session

Tell the owner:
- What was updated in the profile
- What the calibration score means — are we getting closer?
- What Solomon will focus on before the next session

## Rules

- One question at a time during the review.
- Never be defensive about getting something wrong. The point of the session is correction.
- If the owner says something that contradicts the current profile, believe them — update the profile, not your argument.
- The calibration score trend over time is the clearest signal of whether Solomon is working.
- Keep the session focused — no longer than it needs to be.
