---
name: solomon-onboarding-status
phase: interview
description: Shows a checklist of Solomon onboarding sessions — which are complete and which still need to be done. Trigger by saying "onboarding status" or "solomon status".
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding Status

Check which onboarding profile files exist in /opt/data/solomon/profile/ and report the status of each session.

## What to do

Check for the existence of each file and report back as a simple checklist:

- /opt/data/solomon/profile/00-industry.yaml → Session 0: Industry & Sector
- /opt/data/solomon/profile/01-belief-system.yaml → Session 1: Belief System
- /opt/data/solomon/profile/02-why.yaml → Session 2: Why
- /opt/data/solomon/profile/03-principles.yaml → Session 3: Principles
- /opt/data/solomon/profile/04-ideal-outcomes.yaml → Session 4: Ideal Outcomes
- /opt/data/solomon/profile/05-non-negotiables.yaml → Session 5: Non-Negotiables
- /opt/data/solomon/profile/06-taxonomy.yaml → Session 6: Taxonomy

For each file that exists, show the last_updated date from inside the YAML.

## Output format

Solomon Onboarding — Status

[ ] or [x] Session 0: Industry & Sector
[ ] or [x] Session 1: Belief System
[ ] or [x] Session 2: Why
[ ] or [x] Session 3: Principles
[ ] or [x] Session 4: Ideal Outcomes
[ ] or [x] Session 5: Non-Negotiables
[ ] or [x] Session 6: Taxonomy

X/7 complete

If any sessions are incomplete, say: "Say 'start session X' to pick up where you left off."
If all sessions are complete, say: "Onboarding complete. Solomon's foundation is set."
