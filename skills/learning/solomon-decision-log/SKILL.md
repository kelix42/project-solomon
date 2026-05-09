---
name: solomon-decision-log
phase: decision
description: Log a decision that Solomon proposed and the owner's response. Call this every time an action is proposed and the owner responds. Builds the training signal over time.
version: 0.1.0
author: Lynx + Sunny---

# Solomon — Decision Log

Every time Solomon proposes an action and the owner responds, that interaction gets logged here. Over time this builds the clearest possible picture of where Solomon is aligned with the owner and where it keeps getting it wrong.

## When to run this

Call this skill immediately after the owner responds to any proposed action — whether they approved, edited, or rejected it.

## What to log

Append an entry to /opt/data/solomon/decisions/decision-log.yaml in this format:

```yaml
- id: <timestamp YYYYMMDD-HHMMSS>
  date: <human readable date>
  source: <where the decision came from — transcript, mentoring, conversation>
  context: <one sentence describing the situation>
  proposed: <what Solomon proposed>
  owner_response: approved | edited | rejected
  owner_edit: <if edited, what they changed it to>
  rejection_reason: <if rejected, why — capture verbatim if possible>
  learning: <what this tells us about how the owner thinks>
```

## Rules

- Log every decision, even approvals. Approvals are as informative as rejections.
- Capture the owner's exact words when they edit or reject — the language matters.
- The "learning" field is the most important. Don't leave it blank. Even "owner approved without changes — proposal was well-aligned" is useful.
- Never modify past entries. Only append.

## File location

/opt/data/solomon/decisions/decision-log.yaml

If the file doesn't exist yet, create it with an empty list and then append the first entry.
