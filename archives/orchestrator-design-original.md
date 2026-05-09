# The Brain — Master Orchestrator Design Document

**Purpose of this document.** This is the blueprint we will turn into Python code. Every section describes what the system does, when it does it, and the rules it follows. Written in plain English so anyone can read it. When we build the code, each section maps to a module or function.

**What we are building.** A system that learns how a business owner makes decisions, then gradually makes those decisions for them. The system mirrors how a real brain works — it predicts, gets surprised, sleeps, forgets old things, and remembers what matters.

---

## Table of contents

The document is organized in seven clusters. Read top to bottom for a full understanding, or jump to the cluster that fits what you need.

### Orient (start here)
- **Part 0** — The goal
- **Part 1** — The big picture

### Deploy and start (how Solomon is shipped and how a user begins)
- **Part 2** — Architecture and distribution
- **Part 3** — Setup flow
- **Part 4** — Onboarding (the 30-day clone sprint)

### Runtime loop (what happens when an event arrives, in order)
- **Part 5** — Capture
- **Part 6** — Salience scoring
- **Part 7** — The Conductor
- **Part 8** — Classification
- **Part 9** — Non-negotiable check
- **Part 10** — Working memory
- **Part 11** — Multi-lane retrieval
- **Part 12** — Predict before reason (System 1 and System 2)
- **Part 13** — The audit gate
- **Part 14** — Owner state gate (Whoop)
- **Part 15** — The autonomy ladder
- **Part 16** — Logging the decision
- **Part 17** — Action layer and Telegram bot
- **Part 18** — Conversation mode
- **Part 19** — Reports

### Async loops (things that happen later or in the background)
- **Part 20** — Predictions and counterfactuals
- **Part 21** — Mentoring sessions
- **Part 22** — Sleep cycle (nightly jobs)

### Learning (how the brain gets better)
- **Part 23** — Heuristic lifecycle
- **Part 24** — Skills
- **Part 25** — Ingestion (the document pipeline)

### Workforce (how the brain runs the business)
- **Part 26** — The agent workforce (Paperclip integration)

### Operations (implementation details)
- **Part 27** — Storage schema
- **Part 28** — Per-user isolation
- **Part 29** — Configuration
- **Part 30** — Failure modes

### Meta (reference)
- **Part 31** — Build order
- **Part 32** — Glossary
- **Part 33** — How to read this document when building

---

## Quick lookups

**Where do I look if I want to understand…**

- **What Solomon does at a glance** → Part 0, Part 1
- **Where the code runs and where data lives** → Part 2
- **How a new user gets started** → Part 3
- **What happens in the first 30 days** → Part 4
- **How a single decision is made** → Parts 5 through 17
- **How the owner taps Approve / Edit / Discuss** → Part 17
- **How free-form chat with Solomon works** → Part 18
- **What the daily and weekly reports look like** → Part 19
- **What happens at night** → Part 22
- **How rules are born, evolve, and die** → Part 23
- **The full list of skills the orchestrator calls** → Part 24
- **How to add a new skill or workflow** → Part 24
- **How multi-day work gets delegated to AI agents** → Part 26
- **Database tables and columns** → Part 27
- **The order to build things in** → Part 31
- **The meaning of a term I don't recognize** → Part 32

**Names to know up front (full definitions in Part 32):**

- **Solomon** — the product
- **The Brain** — Solomon as a whole system, when speaking in narrative voice
- **The Conductor (= Orchestrator)** — the central routing function inside the worker that calls everything else
- **The skill engine** — the code that loads, validates, runs, and logs skills. Almost every brain operation is a skill the orchestrator calls by name. See Part 24.
- **The desktop app** — small Mac/Windows program on the user's machine, holds credentials and runs the wizard
- **The hosted worker** — always-on per-user process on Render or Railway, where the brain actually runs
- **The Telegram bot** — the only owner-facing interface

---

## Part 0 — The goal

Every design decision in this document points to one outcome: Solomon becomes so much like the owner that it runs the business, and the owner just gets reports.

The owner's relationship with Solomon moves through three phases.

### Phase 1 — Training (the cloning sprint, days 1-30)

The owner runs their business from Telegram. When something happens, Solomon sends one message: a proposed action and three reply options.

```
1  Approve
2  Edit
3  Discuss
```

Every tap is training data. Every edit is a correction Solomon learns from. Every "Discuss" opens a conversation that captures how the owner thinks. The owner does this dozens of times a day. **The 30/80 target:** within 30 days, 80% of daily decisions either ship without asking or land as a one-tap message.

### Phase 2 — Approval (months 2-6, scope by scope)

As Solomon earns trust on a scope, the one-tap messages for that scope stop. Routine work ships on its own and shows up in the morning digest. Higher-stakes scopes still arrive as one-taps, but fewer of them per day. The owner is editing rarely, mostly approving, and starting to read more than they tap.

### Phase 3 — Reporting (month 6+)

Solomon runs operations. Most decisions ship without asking. The owner gets a daily report covering what shipped, what was edited, what hit issues, what was fixed — and a weekly report covering performance, trends, and anything worth attention. Taps still happen for novel or high-stakes events, but they are the exception, not the rhythm.

In Phase 3, multi-day work (campaigns, vendor sourcing, project management) is delegated to a workforce of AI agents that Solomon supervises. The agents work asynchronously through a system called Paperclip; the owner never sees Paperclip directly. The owner sees Solomon's Telegram bot, which reports on what the workforce shipped and asks for approval when an agent's work crosses an owner-defined threshold. See Part 26.

### Conversation runs through all three phases

At any time in any phase, the owner can message Solomon directly — questions, status updates, directives, brainstorming, venting. Solomon answers, captures context, proposes new rules when appropriate. **Every conversation is also training data.** The brain learns from how the owner thinks, not just from what they tap.

### Out of scope

Anything in this spec that does not serve the move from Phase 1 to Phase 3 is out of scope.

---

## Part 1 — The big picture

### What Solomon is, in one paragraph

Solomon is a personal business brain. It learns how a business owner makes decisions and gradually starts making them on the owner's behalf. The owner interacts with Solomon through Telegram. Solomon runs as a hosted worker that is always on, calling Claude for reasoning, storing memories in the user's own Supabase, and using Whoop signals to know how the owner is doing. Over weeks and months, the brain takes on more autonomy and the owner moves from tapping decisions to reading reports.

### The two physical pieces

Solomon runs in two places.

1. **The desktop app.** A small Mac or Windows program installed on the owner's machine. Holds credentials. Runs the setup wizard on first launch. Provides a thin local UI for bulk document uploads. Does not run any of the brain.
2. **The hosted worker.** A small per-user worker process running on Render or Railway. Always on. This is where the brain actually lives: the orchestrator, the Telegram bot, the sleep cycle, the integration adapters, the report generators.

The runtime is the worker. Everything else feeds the worker or is fed by it.

### What the brain is made of, inside the worker

The brain has nine main components. Each has one clear job. They live inside the worker process.

1. **Capture.** Listens to the world (Gmail, Twilio, Plaud, Telegram, Whoop, business webhooks).
2. **Salience scorer.** Decides how much each event matters.
3. **The Conductor (= Orchestrator).** The central routing function. Calls every other component in order.
4. **Storage.** Working memory in Redis, long-term memory in Supabase (Postgres + pgvector).
5. **Reasoning.** Claude API calls in two modes: System 1 (fast, rules) and System 2 (slow, full context).
6. **Audit gate.** A separate Claude call with an audit prompt. Nothing acts without passing through it.
7. **Owner state gate.** Reads Whoop signals (stress, sleep, recovery) and modulates how much autonomy the brain exercises today.
8. **Action layer.** Dispatches approved actions to outbound channels and to the Telegram bot.
9. **Sleep cycle.** Runs at night. Replays the day, tests beliefs, archives rarely-used rules.

These nine components are all wired together by **skills**. Almost every named operation the brain performs (audit gate, intent classification, sleep cycle jobs, mentoring sessions, daily reports, foundation interviews) is implemented as a skill the orchestrator calls by name. The skill engine is the brain's editable layer: change a skill's SKILL.md file and the brain's behavior changes on the next worker redeploy. See Part 24.

The owner experiences all of this through one interface: the Telegram bot.

### How a single event flows through the brain

When something new arrives (an email, a phone call recording, a Telegram message), this is what happens, in order:

1. **Capture** receives the raw event.
2. **Salience scorer** rates it for importance.
3. **The Conductor** classifies the event (what scope, what kind of decision).
4. **The Conductor** checks **working memory** first (fast cache of recent items).
5. If not enough context found, **The Conductor** runs **multi-lane retrieval** on long-term storage.
6. **The Conductor** runs **System 1 prediction** (Claude Sonnet, just rules, no reasoning).
7. **The Conductor** runs **System 2 reasoning** (Claude Opus, full context, real reasoning).
8. **The Conductor** computes the **surprise score** (how far apart S1 and S2 are).
9. **Owner state gate** reads today's Whoop band and sets the effective autonomy ceiling.
10. **The Conductor** sends the proposed action to the **audit gate**.
11. The **audit gate** approves, downgrades, or rejects.
12. If approved, the action is dispatched at the effective autonomy level: act alone, send as Approve/Edit/Discuss in Telegram, or send as suggestion.
13. The **prediction checkpoint** is logged (we expect X to happen by date Y).
14. The **counterfactual** is logged (if we had done the other thing, we expected Z).
15. The decision is written to long-term storage with all metadata.
16. **Working memory** is updated.

That is one full pass. Most of it happens in seconds.

### What the rest of this document covers

After this part, the document follows the natural reading order:

- **Parts 2-3.** Architecture and setup. Where Solomon runs, how a user gets started.
- **Part 4.** The 30-day onboarding sprint. How a new user becomes a cloned user.
- **Parts 5-19.** The runtime loop. Each component in the order it fires for a single event.
- **Parts 20-22.** The async loops. Predictions firing later, mentoring sessions, the nightly sleep cycle.
- **Parts 23-25.** How the brain learns. Heuristic lifecycle, skills, ingestion of historical documents.
- **Parts 26-29.** Implementation details. Database schema, per-user isolation, configuration, failure modes.
- **Parts 30-32.** Meta. Build order, glossary, module map.

---

## Part 2 — Architecture and distribution

### Two pieces

Solomon runs in two places. A small desktop app on the user's machine, and a hosted worker in the cloud. Each has a clear job.

### The desktop app

A small, self-contained application installed on the user's Mac or Windows machine. It does three jobs.

1. Holds the user's credentials in the system keychain (Anthropic key, Supabase URL and key, Redis URL, Telegram bot token, Whoop OAuth tokens, Gmail OAuth tokens).
2. Runs the setup wizard on first launch and on demand.
3. Provides a thin local UI for things that do not fit Telegram. Mainly: bulk document uploads for ingestion (the user drags a folder of historical files into the desktop app, and the app forwards them to the worker).

The desktop app does NOT run the orchestrator, the Telegram bot, the sleep cycle, or any other runtime work. It is a setup and credential tool. The user can close it at any time without affecting Solomon's operation.

### The hosted worker

A small per-user worker process running on Render or Railway. This is where the runtime lives.

- Telegram webhook receiver (Part 17)
- Orchestrator (Part 7)
- Sleep cycle scheduler (Part 22)
- Integration pollers (Whoop every 30 minutes, Gmail webhooks for both incoming email and Plaud-routed transcripts)
- Report generators (daily 7am, weekly Sunday)
- Audit gate, state gate, ingestion pipeline

The worker is always on. It does not depend on the user's machine. The user's laptop can be off for a week and Solomon keeps running.

### Why two pieces

A pure desktop app cannot run the sleep cycle reliably. Laptops sleep, get closed, run out of battery. A pure hosted service would force the user to upload sensitive credentials to the Solomon team's servers, which contradicts the rest of this design. The split is clean: the user owns the credentials and data, the hosted worker is just compute.

### Where everything lives

**On the user's machine:**

- The desktop app binary
- An encrypted credentials file in the system keychain
- A local YAML cache of the wisdom files for fast boot and offline reading
- The setup wizard (browser-based, runs locally during setup)

**In the user's hosted worker (Render or Railway):**

- The orchestrator code
- Telegram bot connection
- Sleep cycle scheduler
- Integration adapters
- Logs (rotated, kept 30 days, stored in Supabase)

**In the user's Supabase:**

- The wisdom files
- The decision log
- Heuristics, foundation files, mentoring history
- Vector embeddings for semantic search
- User skills (Part 24)
- Worker logs

**In the user's Redis:**

- Working memory (Part 10)
- Recent decisions cache
- Rate limit counters

**In the Solomon GitHub repo (public, read-only):**

- Source code (orchestrator, worker, desktop app, wizard)
- System skills (Part 24)
- Installers
- Documentation

### What the user owns

The user owns: their Anthropic account, their Supabase project, their Redis Cloud database, their Render or Railway account, their Telegram bot, their Whoop account, their Gmail account, and every wisdom file, decision log, heuristic, and learned skill produced by the brain.

### What Solomon (the project) provides

The desktop app, the hosted worker code (deployed to the user's own Render or Railway by the wizard), the bundled system skills, and updates to all of those.

If Solomon (the project) shuts down tomorrow, every user's brain keeps running. The code is theirs (open source on GitHub), the data is theirs (Supabase, Redis), the infra is in their accounts.

### Cost

The user pays directly to:

- Anthropic for Claude API usage (rough range $20 to $100 per month per user, depending on volume)
- Render or Railway for the worker (about $5 to $7 per month)
- Supabase (free tier covers most users at start, $25 per month if scaled up)
- Redis Cloud (free tier sufficient at start)
- Whoop subscription if applicable

Solomon (the project) bills the user nothing for software. Pricing models for support, premium skills, or managed offerings are out of scope for this spec.

### Updates

When Solomon ships a new release:

1. The desktop app checks for updates on launch and prompts to install.
2. After the desktop app updates, it triggers a worker redeploy on the user's Render or Railway. The worker rebuilds from the new release tag and restarts.
3. Database migrations run automatically on worker start. Schema changes are versioned and idempotent.
4. Bundled system skills update with the release. User skills are untouched.

Workers redeploy in under a minute. Brief Telegram outages during redeploy are acknowledged in the next outbound message.

### Observability

Worker logs and Claude API traces are stored in the user's own Supabase. Solomon (the project) does not collect telemetry by default. A future opt-in shared error reporting layer (Sentry-style, anonymized) is possible but out of scope for this spec.

### Backup and recovery

The desktop app exposes Export and Import.

- **Export** packages the user's Supabase data, configuration, and credentials manifest into a single encrypted archive. The user keeps it.
- **Import** restores from an export file. Used for moving to a new machine, recovering from an accidentally deleted Supabase project, or migrating to a new Solomon (the project) release that requires a clean reinstall.

Decision log size grows over time. Exports are incremental after the first full export.

### Multi-machine

If the user installs Solomon on a second machine (laptop and desktop, for example):

1. They run the wizard. Pick "I already have Solomon set up."
2. Enter the user's worker URL.
3. The wizard pulls credentials from a one-time encrypted handoff. The first machine generates a 6-character pairing code; the second machine enters it; credentials transfer over the worker.

Both desktop apps point to the same worker. The worker does not care how many desktops the user runs. There is no syncing problem because the worker is the single source of truth and the desktops only hold credentials.

---

## Part 3 — Setup flow

### Goal

Get the user from clicking download to having their first Telegram conversation with Solomon, in under 30 minutes.

### Step 1. Download

The user opens the Solomon Releases page on GitHub. Downloads `Solomon.dmg` (Mac) or `Solomon.exe` (Windows).

### Step 2. Install

Open the file. Drag to Applications (Mac) or run the installer (Windows). Launch. A small icon appears in the menu bar (Mac) or system tray (Windows). Solomon sets itself to launch on login.

### Step 3. Wizard opens

On first launch, Solomon opens the user's default browser to a local setup page. The wizard walks through 10 screens. The user can pause at any step and resume later. State is saved locally.

**Screen 1. Welcome.** Brief explanation. The wizard checks whether Telegram is installed on the machine and shows confirmation. If Telegram is missing, a button opens telegram.org for download.

**Screen 2. Connect to Claude.** Enter the Anthropic API key. A side panel offers a link to console.anthropic.com to create a key for users who do not have one. Live validation.

**Screen 3. Long-term memory (Supabase).** A button opens supabase.com to create a free project. The wizard asks for project URL and anon key. Solomon runs the bootstrap migration: creates every table the orchestrator and skills will write to, enables pgvector, creates Storage buckets for foundation files and ingested documents, and seeds the `skill_registry` table from the bundled system skills (so every skill the orchestrator might call has a row before any user activity begins). The full list of tables and skill outputs created here is in Parts 24 and 26. Live validation confirms the migration completed.

**Screen 4. Working memory (Redis).** A button opens redis.com to create a free Redis Cloud database. The wizard asks for connection string. Live validation.

**Screen 5. Provision the worker.** The most complex screen. Help text and screenshots are essential.

The wizard walks through:

1. Sign up or log in to Render or Railway.
2. Click the "Deploy Solomon" button (a one-click deploy template the project maintains).
3. The deploy template asks for: Anthropic key, Supabase URL and key, Redis URL, Telegram bot token (set later, can leave blank), GitHub release tag.
4. Render or Railway provisions the worker in a few minutes.
5. The user copies the worker URL back into the wizard.
6. Live validation: the wizard pings the worker and gets a heartbeat.

**Screen 6. Create the Telegram bot.** A button opens BotFather inside the Telegram app via deep link. Three numbered steps with screenshots: name the bot, copy the token. The wizard validates the token and sets the bot's webhook URL to point to the user's worker.

**Screen 7. Connect Gmail (recommended).** OAuth flow. The wizard pops up Google's consent screen. The user authorizes Solomon to read their Gmail. Tokens are stored encrypted on the user's machine and forwarded to the worker.

**Screen 8. Connect Whoop (recommended).** OAuth flow. The user authorizes Solomon to read their Whoop data. Same token flow as Gmail. If the user does not have Whoop, they can skip. The state gate (Part 14) defaults to yellow band permanently in that case, which is more conservative.

**Screen 9. Connect Plaud (optional).** For users with a Plaud device. There is no direct Plaud API integration. Instead, the wizard walks the user through configuring Plaud's AutoFlow feature to email transcripts to their Gmail (which Solomon already reads).

Three numbered steps with screenshots:

1. Open the Plaud app, go to AutoFlow, create a new flow.
2. Set the trigger: "When recording is synced." Set the action: "Email transcript to" with the user's own Gmail address. Choose Transcript content type. Save and enable.
3. The wizard waits for the user to record a short test recording (at least 5 minutes / 200+ words, since AutoFlow has a minimum). Once the test transcript hits Gmail, the wizard's live indicator confirms.

The Gmail adapter (Part 5) is told to filter messages from Plaud's sender address into a Plaud event handler. No new credentials are needed beyond Gmail itself.

If the user does not have Plaud, they skip this screen. Solomon still works fine without it.

**Note on the future.** Plaud is building an "application API" that will let third parties read transcripts from existing Plaud accounts directly. When that ships, Solomon swaps to the API and retires this AutoFlow-based path. Until then, AutoFlow + Gmail is the supported path.

**Screen 10. Test contact.** A button opens the new bot in Telegram. The wizard waits for the first message. As soon as the user sends any message to the bot, the worker receives it (proving the entire chain works), the wizard flips to confirmed and closes.

### Step 4. Bot speaks first

Inside Telegram, the bot sends:

> Hi. I'm Solomon. Ready to start creating your brain?
>
> [ Yes, let's go ]   [ Not yet ]

Tapping "Yes" loads the `industry-business-interview` skill and starts the foundation interviews (Part 4). Tapping "Not yet" saves state and tells the user to message any time when ready.

### Step 5. Foundation sprint begins

The 30-day cloning sprint (Part 4) starts. The wizard's job is done. From here, everything happens in Telegram.

### Re-running the wizard

The wizard can be re-run from the desktop app menu (Reset, then Reconfigure). Two reset levels:

- **Soft reset.** Replace credentials but keep all wisdom files, decision log, heuristics. Useful for switching to a new bot or rotating API keys.
- **Hard reset.** Wipe Supabase, Redis, restart with a fresh wizard. The data in Supabase is preserved in the user's account (the project never deletes the user's data remotely; the user does that in Supabase if they want).

### Module ownership

- `desktop/main.py` — desktop app entry point, menu bar icon, system tray
- `desktop/credential_vault.py` — keychain integration
- `desktop/upload_ui.py` — bulk document upload UI
- `wizard/server.py` — local web server for the wizard
- `wizard/screens/*.py` — one file per wizard screen
- `wizard/integrations/*.py` — OAuth flows for Gmail and Whoop; Plaud configuration helper (no OAuth, walks the user through AutoFlow setup)
- `wizard/worker_provisioner.py` — Render or Railway deploy automation
- `worker/main.py` — hosted worker entry point
- `worker/health.py` — heartbeat endpoint for wizard validation

---

## Part 4 — Onboarding (the 30-day clone sprint)

This part covers the first 30 days of a new user's life with the brain. The target — set in Part 0 — is that by day 30, 80% of the owner's daily decisions either ship without asking or land in Telegram as a one-tap message. The whole onboarding design serves that target.

The original spec had a 1-2 week interview followed by a separate 30-day observe-only mode. That is gone. The interview, ingestion, shadow mode, and live suggestions overlap and run in parallel. The brain starts producing useful output in week 2.

**Model selection rule for Stage 1.** Every Claude call made during onboarding (this Part) and ingestion (Part 25) uses the most powerful Claude model currently available — at the time of writing, Claude Opus 4.7. Stage 1 is high-stakes and infrequent per user. Cost difference is irrelevant on a one-time basis. Stage 2 (live operations) makes the opposite tradeoff: System 1 uses Sonnet for speed; System 2 and audit gate use Opus.

**All Stage 1 outputs are living documents.** The industry profile, foundation YAMLs, seeded heuristics, and ingested decision history are starting points, not fixed truth. They keep changing after day 30.

### The 30-day timeline at a glance

| Days | Phase | What happens |
|---|---|---|
| 1-3 | Foundation interviews | 6 voice sessions via Telegram bot. Foundation YAMLs written. Industry profile committed. |
| 1-7 | Bulk ingestion (parallel) | Owner uploads emails, transcripts, contracts, SOPs. Pipeline classifies, extracts decisions, mines heuristics. |
| 4-7 | Heuristic review | Owner reviews mined and seeded heuristics in Telegram, taps approve / edit / reject. |
| 4-7 | Integration setup | Gmail, Twilio, calendar, Plaud, Whoop connected. |
| 8-14 | Shadow + suggest mode | Brain captures every event. For each, sends a Telegram message: "If I were running this, I'd do X. Tap 1/2/3." Owner taps through hundreds of decisions per week. |
| 15-21 | First promotions | Scopes that hit sprint thresholds (20 decisions, <10% override, >0.7 confidence) get promoted to act-with-approval. Low-stakes scopes auto-promote without an approval click. |
| 22-30 | Auto-pilot for routine work | Most operational scopes are act-with-approval (one-tap) or act-alone. Higher-stakes scopes still in suggest. By day 30, 80% of daily decisions are auto or one-tap. |

### Goal of onboarding

By the end of day 30, the brain has:
- An industry profile that establishes the operating context
- Foundation YAML files filled in (beliefs, why, principles, non-negotiables, ideal outcomes, nice-to-haves)
- Initial taxonomy (scopes, domains, decision types relevant to this business), with each scope tagged `low_stakes` or `high_stakes`
- Initial heuristics from interview seeding and ingestion mining (target: 80-150 heuristics)
- Initial skill playbooks for the most common multi-step processes
- Connected integrations including Whoop and the Telegram bot
- A historical context bank from ingested documents
- 200+ decisions logged with owner taps (the data needed for promotion decisions)
- A subset of scopes already at act-with-approval or act-alone

**There is no separate observe-only phase.** The brain starts sending suggestions on day 8 and learns from every owner tap. Suggest mode IS the observation phase.

### Step 1 — Industry & business model (day 1, ~60 min)

The owner picks a primary industry and sub-specialty from a structured list (Real Estate → House Flipper / Rental Landlord / BRRRR / Wholesaler; Construction → GC / Electrician / Plumber; Legal, Marketing, Healthcare, etc.). Then they describe the business model in their own words.

Conducted via Telegram bot. The user types their answers (Wispr Flow or any voice-to-text input is recommended for fast typing, but everything that reaches Solomon is text). Claude (Opus 4.7) asks follow-up questions. Output: `industry_profile.yaml` written to the user's Supabase.

The profile contains: `industry`, `sub_specialty`, `business_model_summary`, `key_terminology`, `typical_workflows`, `common_counterparties`, `geographic_scope`, `top_pain_points`.

**Why first.** A real-estate flipper's "pricing" decisions don't share vocabulary with a marketing agency's. Without industry context, every later step is miscalibrated.

### The structured interview (days 1-3)

Six fixed sessions, conducted as text conversations through the Telegram bot. The owner can do them in one afternoon or spread them across three days. Average total time: 5-6 hours of owner attention, compressed by removing the conversational filler that ate 60-90 minutes per session in the original spec. The bot drives a tight curriculum and asks only the follow-ups that matter. The user types replies directly in Telegram (Wispr Flow or any phone voice-to-text is recommended for speed, but the bot only ever receives text).

**Session 1 — Belief and worldview (~45 min).**
How the owner sees the world, faith or philosophy if any, how they think about right and wrong, risk, people. Output: `belief_system.yaml`.

**Session 2 — The why (~30 min).**
Why this business exists. What the owner would do if money weren't the question. Output: `why.yaml`.

**Session 3 — Principles (~60 min).**
Personal rules that shape decisions. For each, an example of how it shows up in practice. Output: `principles.yaml`.

**Session 4 — Ideal outcomes (~45 min).**
What winning looks like across money, customer trust, employee retention, reputation, personal time, family. Owner ranks them. Output: `ideal_outcomes.yaml`.

**Session 5 — Non-negotiables (~60 min).**
Hard rules. Each paired with: scope, reasoning, and a check pattern. Output: `non_negotiables.yaml`. These remain the most stable foundation file.

**Session 6 — Domain map (~60 min).**
What kinds of decisions the owner actually makes. Walking through a typical week. Each scope is tagged `low_stakes` or `high_stakes` to enable later auto-promotion logic. Output: `taxonomy/scopes.yaml`, `taxonomy/domains.yaml`, `taxonomy/decision_types.yaml`. Plus the integration list.

### How sessions work in practice (Telegram-native)

Sessions run inside the Telegram bot. There is no web app for onboarding.

1. Bot announces session at the scheduled time: "Ready for Session 3 — Principles? Reply START to begin or LATER to delay."
2. Bot sends one question. Owner replies in Telegram with a typed message (using Wispr Flow or phone voice-to-text if they prefer to speak; the bot still only receives text).
3. Claude generates a follow-up only if the answer was thin.
4. After every 3-4 questions, the bot sends a summary: "Here's what I heard. Reply OK or send corrections."
5. Owner edits by replying with the corrected text. Edited version is the truth.
6. End of session: bot writes YAML files to Supabase (and mirrors them to the local cache). Owner gets a one-line confirmation with a link to the diff if they want to see it.

### Why the curriculum is fixed

A fixed curriculum means every user gets the same depth, the curriculum can be improved across users, and edge cases are caught reliably. Adaptive question generation comes later in ongoing mentoring (Part 21).

### Ingestion runs in parallel (days 1-7)

The moment the owner connects Gmail and uploads any document backlog, the ingestion pipeline (Part 25) starts processing. It does not wait for interviews to finish. By day 7, ingestion has typically:
- Classified every uploaded document
- Extracted historical decisions
- Mined candidate heuristics

These mined heuristics arrive in the owner's Telegram queue alongside interview-seeded heuristics for tap-through review.

### Initial heuristic seeding (days 4-7)

Two paths feed the initial heuristic set:

**Interview seeding.** Claude reads all 6 session transcripts and proposes heuristics from owner-stated rules. Example:
> "In session 3 you said 'I always pay above market when someone has been with us 3+ years.' Save as a heuristic in compensation? 1 Save  2 Edit  3 Don't save"

Approved → `source: onboarding`, `initial_confidence: 0.7`.

**Ingestion mining.** The pipeline detects repeated patterns in historical documents. Example:
> "I see 23 of 31 after-hours quotes priced 20-25% above base. Make this a heuristic? 1 Save  2 Edit  3 Don't save"

Approved → `source: ingestion`, `initial_confidence: 0.5`.

Both paths produce Telegram one-tap reviews. Target: 80-150 approved heuristics across both paths by end of day 7.

### Domain-specific onboarding modules (days 4-7, optional)

After the 6 core sessions, the `industry-module-generator` skill runs. It reads the user's industry profile and dynamically generates a follow-up curriculum tailored to their sub-specialty. For a flipper: targeted questions about ARV calculation, contractor markups, scope-of-work patterns. For a rental landlord: lease terms, maintenance triage, screening rules. For a marketing agency: project intake, scope creep handling, billing cadence. The skill is one piece of code, not a library of pre-written modules. Output: industry-specific seed heuristics.

These modules are pluggable and reused across users. We build them once per sub-specialty.

### The shift to live (day 8)

On day 8, the brain switches from setup to live mode. Every event from that point forward triggers the full process_event pipeline (Part 7). The autonomy level for every scope starts at `suggest`. This means: every audit-approved action becomes a Telegram one-tap message asking the owner to ship, edit, or skip.

The owner is now tapping their way through real decisions. Each tap generates training data:
- `1 Approve` (no edit) = success signal, +increment confidence
- `2 Edit` then send = correction signal, comparator for the next sleep cycle
- `3 Discuss` = opens conversation; the brain learns from the dialog. If the owner ultimately chooses not to ship, this counts as override (×0.85 confidence). If the conversation reveals a missing rule, that rule is captured as a heuristic candidate.

By volume: an active flipper generates 30-80 events per day. Over 7 days that is 200-500 decisions across all scopes. This is the volume that makes promotions possible.

### Promotions during the sprint (days 15-30)

Job 7 (autonomy re-evaluation) runs every night and applies sprint thresholds (Part 15): 20 decisions, <10% override, >0.7 confidence. Scopes meeting these flag `ready_for_promotion`.

For scopes tagged `low_stakes: true` (appointment confirmations, FAQ replies, simple calendar shuffles), auto-promotion fires the same night with a morning notification. For `high_stakes: true` scopes (pricing, hiring, contracts), the brain proposes promotion in Telegram and waits for owner approval.

By day 30, the typical owner has:
- 4-8 scopes at `act_alone` (low-stakes, high-volume routine work)
- 6-12 scopes at `act_with_approval` (one-tap operational decisions)
- 3-5 scopes at `suggest` (high-stakes work that still needs review)
- 0-2 scopes at `watch` (rare or unfamiliar territory)

If the percentage of decisions hitting auto or one-tap reaches 80%, the 30/80 target is met. If it hasn't, day 30 triggers a "calibration mentoring session" that reviews the gap.

### Whoop is required during the sprint

Stress and sleep gating (Part 14) is on from day 8 forward. The compressed timeline means the brain is taking more risk earlier than the original spec, and the owner state gate is the safety valve. On red-band days during weeks 2-4, the brain's effective autonomy ceiling drops to suggest, regardless of the static autonomy level. This protects the owner from the brain learning bad lessons from bad-state days.

### When onboarding is "done"

The hard requirements:
- All 6 core sessions complete
- Foundation YAML files all have content
- The industry module generator has run for the user's sub-specialty
- At least 5 days of historical document ingestion processed
- 80+ heuristics approved
- Whoop connected and producing readings
- Telegram bot connected with a verified chat_id
- 200+ live decisions logged with owner taps

Calendar time: ~30 days. Owner attention: ~10-15 hours total spread across the month.

### Module ownership

When we build:
- `onboarding/industry_selector.py` — industry & sub-specialty picker, follow-up loop, `industry_profile.yaml` writer
- `onboarding/curriculum.py` — fixed curriculum for each session
- `onboarding/telegram_session_runner.py` — session flow and state machine over Telegram
- `onboarding/foundation_writer.py` — generates and commits YAML files
- `onboarding/seed_heuristics.py` — extracts initial heuristics from session transcripts
- `onboarding/sprint_tracker.py` — tracks 30-day sprint progress, computes the 80% metric, schedules calibration session if missed
- `onboarding/industry_module_generator.py` — generates the follow-up curriculum dynamically based on the user's industry profile

---

## Part 5 — Capture (how the brain listens)

### What it does

Watches all the channels where decisions happen. Every new event becomes a `RawEvent` object.

### Sources

Each source has a small adapter that converts its raw format into a standard `RawEvent`.

- **Gmail API** — webhook fires on new email. Pulls full thread.
- **Twilio** — webhook fires on new call or SMS. For calls, fetches recording and runs Whisper.
- **Plaud** — transcripts arrive via the user's Gmail. Plaud's AutoFlow feature is configured during setup to email each new transcript to the user's Gmail. Solomon's Gmail adapter filters by Plaud's sender address and routes matching messages to a Plaud-specific event handler that strips the email wrapper, extracts the transcript body, and creates a `RawEvent` with `source = plaud`. There is no direct Plaud API integration today — Plaud's developer platform exists but does not let third parties read existing Plaud accounts. AutoFlow has a 200-word minimum, so very short recordings do not generate transcripts. This is acceptable: short recordings have low salience anyway.
- **Telegram bot** — text messages from the owner (typed directly or via Wispr Flow / phone voice-to-text). The bot only ever receives text. Replies of "1", "2", or "3" to a pending suggestion are routed to the approval handler, not treated as new events.
- **Whoop API** — pulls daily readiness, recovery, sleep, strain, and stress signals. Polled every 30 minutes during owner waking hours. Fed to the owner state gate (Part 14).
- **Webhooks from business tools** — CRM updates, calendar changes, accounting events.

### What a RawEvent looks like

```
RawEvent:
  id: unique identifier
  source: which channel (gmail, twilio, plaud, voice_note, crm, etc.)
  received_at: timestamp
  participants: list of people involved
  raw_content: the original text or transcript
  channel_metadata: extra info (subject line, phone number, calendar event id, etc.)
```

### Rules

- **Every event gets a unique id immediately.** No duplicates.
- **Raw content is never deleted.** Even if we extract a clean version, the original stays for audit.
- **Events that look like duplicates** (same content from multiple channels) are linked, not merged.

### What happens next

The RawEvent is dropped into a queue. The Salience scorer picks it up.

---

## Part 6 — Salience scoring (how much does this matter)

### What it does

Looks at the RawEvent and decides how much attention to give it. Not all events are equal.

### What it scores

Four factors. Each scored 0.0 to 1.0. Then averaged with weights.

1. **Stakes** — how big is the decision? (dollar amount, relationship value, reversibility)
2. **Novelty** — have we seen something like this before? (low novelty = familiar; high = strange)
3. **Emotion** — does the language signal urgency, frustration, gratitude, fear?
4. **Owner involvement** — did the owner act personally, or was this routine?

### How it scores

A single Claude call with a tight prompt:

> "Read this event. Rate it on stakes, novelty, emotion, owner involvement, each 0.0 to 1.0. Return a JSON object."

The four scores are averaged with weights (configurable per business — default: stakes 40%, novelty 30%, emotion 15%, owner involvement 15%) into a final `salience_score`.

### What the score means

- **Below 0.2** — low salience. Logged with minimal extraction. No embedding. Skip the pattern engine.
- **0.2 to 0.6** — medium. Standard processing.
- **Above 0.6** — high. Full extraction. Embedded. Marked "hot" for retrieval. Flagged for next mentoring session if still uncertain after reasoning.

### Why this matters

Without salience, the brain would treat a $50 invoice the same as a $50,000 contract. Salience is the brain's first filter — what to think hard about, what to skim past.

---

## Part 7 — The Conductor (Orchestrator)

The Conductor (a.k.a. the Orchestrator — same thing, different name in the visual diagram vs. the code) is where everything gets called from. This is where most of the Python code lives. It is *not* the Brain in the system-wide sense; it is one component within the Brain.

### Core function: `process_event(raw_event)`

The Conductor runs this function every time a new event is ready.

In plain English:

```
def process_event(raw_event):
  # Step 1 — Classify
  scope, domain = classify(raw_event)

  # Step 2 — Check non-negotiables fast
  if violates_non_negotiable(raw_event, scope):
    escalate_to_owner(raw_event, reason="non-negotiable violation")
    return

  # Step 3 — Pull working memory (fast)
  hot_context = working_memory.fetch(scope, raw_event.participants)

  # Step 4 — Pull long-term memory if needed
  if hot_context.is_thin():
    long_context = multi_lane_retrieval(raw_event, scope, domain)
  else:
    long_context = empty()

  # Step 5 — Bundle context
  context = bundle(hot_context, long_context, foundation_files(scope))

  # Step 6 — Predict (System 1 — fast, rules only)
  s1_answer = system_1_predict(raw_event, context.heuristics_only())

  # Step 7 — Reason (System 2 — slow, full context)
  s2_answer = system_2_reason(raw_event, context.full())

  # Step 8 — Compute surprise
  surprise = divergence(s1_answer, s2_answer)

  # Step 9 — Audit gate
  audit_verdict = audit_gate.run(s2_answer, context, surprise)

  # Step 10 — Compute today's effective autonomy ceiling from Whoop
  effective_level = owner_state_gate.modulate(autonomy_level(scope))

  # Step 11 — Act based on verdict and effective autonomy level
  if audit_verdict == "approve" and effective_level == "act_alone":
    execute(s2_answer)
  elif audit_verdict == "approve" and effective_level == "act_with_approval":
    telegram.send_one_tap(s2_answer)   # 1 Approve / 2 Edit / 3 Discuss
  elif audit_verdict == "approve" and effective_level == "suggest":
    telegram.send_suggestion(s2_answer)
  elif audit_verdict == "downgrade":
    telegram.send_suggestion(s2_answer)
  else:  # reject
    telegram.escalate(raw_event, s2_answer, audit_verdict)

  # Step 12 — Log everything
  log_decision(raw_event, s1_answer, s2_answer, surprise, audit_verdict, context)

  # Step 13 — Store predictions and counterfactuals
  store_prediction(s2_answer, expected_by, expected_outcome)
  store_counterfactual(s2_answer, alternative_choice, alternative_outcome)

  # Step 14 — Update working memory
  working_memory.update(raw_event, s2_answer)
```

The next sections explain each piece in detail.

---

## Part 8 — Classification

### What it does

Looks at the event and decides:
- **Scope** — what part of the business is this about? (pricing, hiring, scheduling, vendor relations, etc.)
- **Domain** — narrower than scope (corporate cleaning quote, employee discipline, vendor renewal, etc.)
- **Decision type** — is this a quote, a complaint, a scheduling change, a strategic choice, a policy question, etc.

### How it does it

One Claude call with a strict prompt that returns structured JSON. The prompt includes the current taxonomy of scopes and domains (loaded from a YAML file) so Claude doesn't invent new tags.

### Rules

- **Tags must come from the existing taxonomy.** If Claude wants to suggest a new tag, that goes into a "tag suggestions" queue for owner review during mentoring.
- **Multi-scope events get multiple tags.** A complaint about pricing on a hiring decision is tagged both.
- **Confidence on the classification itself is logged.** Low-confidence classifications get a second look.

---

## Part 9 — Non-negotiable check

### What it does

Before the system spends compute on reasoning, it checks if the event would lead to a non-negotiable violation.

### How it does it

The non-negotiables are stored in `non_negotiables.yaml` (stored in Supabase, mirrored as YAML in the local cache). Each non-negotiable has:
- A description ("never work on Sundays")
- A scope (when it applies)
- A check function or pattern

The Orchestrator loads the relevant non-negotiables for the event's scope and runs each check.

### If a violation is detected

The system escalates immediately. No reasoning, no action, no Claude call. The owner gets a message: "Event X looks like it would violate non-negotiable Y. Should I act anyway, or skip?"

### Why this is first

It's cheap. It saves compute. And it prevents the brain from ever drafting something that violates a hard rule.

---

## Part 10 — Working memory (the hot cache)

### What it is

A small, fast, short-lived store of "what's currently active." Lives in Redis (or a Postgres table with TTL).

### What goes in it

- **Open items** — deals, jobs, threads that are not closed yet
- **Last 7 days of decisions** — for fast context on follow-ups within the typical response window
- **Active mentoring topics** — what the owner has recently discussed
- **Recently elevated heuristics** — rules that were updated or surprised in the last week

### How it gets populated

- Every new event with high salience adds an entry.
- Every Action that opens a new thread (sends an email, creates a deal) adds an entry.
- Items expire automatically: 7 days of inactivity = drop out.
- Items "graduate" out: deal closes, job done, complaint resolved.

### Capacity

Capped at about 50 items. When full, lowest-salience oldest item is evicted first.

### Why this exists

When a client emails about a deal, the brain shouldn't have to re-embed and search the entire history. The deal is already in working memory. Faster, cheaper, more like how humans actually think.

---

## Part 11 — Multi-lane retrieval

### What it does

When working memory is thin, the Orchestrator does a deeper pull from long-term storage. Not one query — five, in parallel.

### The five lanes

1. **Semantic lane** — pgvector similarity. "Find decisions that mean something similar."
2. **Recency lane** — last N decisions in this scope. "What have we been doing lately?"
3. **Entity lane** — decisions involving the same client, employee, or vendor. "What's our history with this person?"
4. **Pressure lane** — decisions made under similar time/financial pressure. "How do we handle pressure like this?"
5. **Foundation lane** — non-negotiables and principles for this scope. "What rules apply here?"

### How they combine

Each lane returns a ranked list. The Orchestrator combines them with weighted scoring. Default weights:
- Semantic: 30%
- Recency: 20%
- Entity: 25%
- Pressure: 15%
- Foundation: 10%

(Weights are configurable per domain.)

### Decay applied at retrieval

Every retrieved item gets multiplied by a recency factor:
```
final_score = lane_score * exp(-decay_rate * days_since_last_retrieved)
```

Items not retrieved or referenced in 90 days fall to near-zero relevance, even if they were highly ranked.

### Output

Top 10 to 15 items across all lanes (deduplicated).

---

## Part 12 — Predict before reason (System 1 and System 2)

### What System 1 does

A fast Claude call (Sonnet) with a strict prompt:

> "Here are the relevant heuristics. Here is the situation. Don't reason. Don't think hard. Just pattern-match and answer: what would these rules say to do?"

The output is short, often one or two lines. The model doesn't get the full context — only the heuristics.

### What System 2 does

A deeper Claude call (Opus) with everything:

> "Here is the full situation, the past decisions, the foundation principles, the relevant heuristics. Reason carefully. What is the right thing to do here, and why?"

The output is fuller — a proposed action plus reasoning.

### How they're compared

The Orchestrator computes a `divergence_score`:
- 0.0 = the two answers say the same thing
- 1.0 = the two answers contradict each other completely

This is the **surprise score** of the decision.

### What happens based on divergence

- **Low divergence (< 0.2)** — System 1 and System 2 agree. This decision is "settled." Ship the System 1 answer (faster, cheaper). Log normally.
- **Medium divergence (0.2 to 0.6)** — Some disagreement. Ship System 2 (the careful answer). Log the gap as a learning event.
- **High divergence (> 0.6)** — Major disagreement. Ship System 2 but flag it: the rules don't capture the reasoning. This decision becomes a top-priority mentoring topic.

### Why this matters

Every divergence is a sign that the heuristics are out of date. The brain learns by paying attention to the gap between what it would have done and what it should have done.

---

## Part 13 — The audit gate

### What it is

A separate Claude call. Same model family as Reasoning, but a different prompt and a different role: it audits the proposed action before it ships.

### What it checks

The audit gate receives the proposed action plus all the context. It runs through a checklist:

1. **Hard-rule check** — does this violate any non-negotiable? If yes, REJECT.
2. **Confidence check** — is the confidence on the action high enough for the current autonomy level on this scope? If not, DOWNGRADE.
3. **Scope check** — is this action within the bounds the Brain was authorized to do? If not, DOWNGRADE or REJECT.
4. **Coherence check** — does the action line up with the foundation principles and recent decisions? If not, DOWNGRADE.
5. **Tone check** — does the output sound like the owner? If brand voice is off, DOWNGRADE.

### What the audit gate returns

One of four verdicts:
- **APPROVE** — ship it.
- **DOWNGRADE** — ship it as a suggestion to the owner instead of an autonomous action.
- **REJECT** — don't ship anything. Escalate to owner with reason.
- **REQUEST_RETHINK** — send back to the Conductor with feedback. The Conductor runs System 2 again with the audit gate's notes added to context.

### The audit gate uses the deeper model

For audit gate calls, use Opus. The audit role is high-stakes and infrequent enough to justify the cost.

### The audit gate logs everything

Every audit gate verdict gets stored: input action, verdict, reasoning. This is its own audit trail. If the Brain starts shipping bad decisions, the audit log shows where it failed.

---

## Part 14 — Owner state gate (Whoop)

### What it is

A real-time check that reads the owner's biometric state and modulates today's effective autonomy ceiling. Static autonomy levels say what the brain has earned the right to do. The owner state gate decides what it should actually do today, given how the owner is showing up.

### Why it exists

Stress and sleep deprivation produce decisions the owner regrets. If the brain has been cloning itself off recent decisions made under high stress and low sleep, it has been learning the wrong things. The state gate also protects the owner: on a 4-hour-sleep day, the brain holds back instead of acting boldly on the owner's behalf.

### Inputs

Pulled from the Whoop API every 30 minutes during waking hours:
- `recovery_score` — 0-100, daily
- `sleep_performance` — 0-100, last sleep
- `sleep_hours` — actual hours slept last night
- `strain_yesterday` — 0-21
- `current_stress_band` — low / moderate / high (Whoop's stress monitor)

### Modulation rules

Each morning at wake, the gate computes today's `state_band`:

```
if recovery_score >= 67 AND sleep_hours >= 7:
  state_band = "green"
elif recovery_score >= 34 AND sleep_hours >= 5:
  state_band = "yellow"
else:
  state_band = "red"
```

During the day, if `current_stress_band` flips to `high` for more than 30 minutes, the band drops one level (green → yellow, yellow → red) until it recovers.

### Effect on autonomy

```
green   →  effective_level = scope's static autonomy level (no change)
yellow  →  effective_level = min(static, "act_with_approval")
              i.e. act-alone scopes drop to one-tap approval for the day
red     →  effective_level = min(static, "suggest")
              i.e. nothing ships without an explicit owner action
```

A non-negotiable violation always escalates regardless of band.

### What the owner sees

On red days, the morning Telegram digest opens with:

> Recovery 28, slept 4h12m. Holding everything in suggest mode today. 14 decisions waiting in the queue when you're ready.

The owner can override with `/force_normal` if they explicitly want the brain to operate at full autonomy despite the signals.

### What gets logged

Every decision logs the `state_band` at decision time and the `effective_level` used. Sleep cycle Job 7 uses this when re-evaluating autonomy: decisions made on red days don't count against override rate (the owner was tired, of course they edited more) and don't count toward promotion thresholds (we don't promote based on red-day data).

### Failure modes

- **Whoop API unreachable.** Default to `yellow`. The brain doesn't know how the owner is doing, so it holds back.
- **Owner not wearing Whoop.** Same as above: yellow until the band reads.
- **Stale data (last reading > 6 hours old).** Default to yellow.

### Module ownership

- `state_gate/whoop_client.py` — API calls, polling, caching
- `state_gate/band_calculator.py` — band computation rules
- `state_gate/modulator.py` — autonomy modulation logic
- `state_gate/state_log.py` — per-decision state band logging

---

## Part 15 — The autonomy ladder

### What it is

Each scope (pricing, hiring, scheduling, etc.) has its own autonomy level. The level dictates what happens after the audit gate approves.

### How autonomy grows over time

The autonomy level for each scope is not fixed. It moves up and down based on the brain's track record in that scope. Trust is earned through consistent performance, and revoked the moment performance breaks.

**A typical journey, by week.**

This timeline assumes the 30-day onboarding sprint described in Part 4. Sprint thresholds (lower bars) apply for the first 30 days; production thresholds (higher bars) apply after.

**Week 1.** User onboards. Foundation interviews via Telegram. Ingestion runs in parallel. By end of week, 80-150 heuristics seeded and approved by owner taps.

**Week 2.** Brain goes live in `suggest` mode across all scopes. Every audit-approved action arrives in Telegram as a one-tap suggestion. Owner taps through 30-80 events per day. Each tap is training data.

**Week 3.** First promotions. Scopes hitting sprint thresholds (20 decisions, <10% override, >0.7 confidence) flag `ready_for_promotion`. Low-stakes scopes auto-promote to `act_with_approval` with morning notification. High-stakes scopes propose promotion via Telegram and wait for the owner's tap.

**Week 4.** Second promotions. The earliest-promoted scopes have now run at `act_with_approval` for ~10 days at <5% override and qualify for `act_alone`. By end of week, the typical owner has 4-8 scopes at `act_alone`, 6-12 at `act_with_approval`, 3-5 at `suggest`, 0-2 at `watch`. The 30/80 target is hit if 80% of the day's decisions land in the act-alone or one-tap categories.

**Months 2-3.** Production thresholds take over. Promotion to `act_alone` now requires 50 decisions and <5% override. Most scopes that earned trust during the sprint stay there; new scopes (or scopes where the world changed) cycle through suggest → act-with-approval at the slower production pace.

**Demotion happens automatically.** Override rate above 15% in any week drops the scope one level. A non-negotiable that slips through drops the scope to `watch` and logs an incident. Edit rate above 30% in a week drops the scope one level. These checks run every night as Job 7 of the Sleep cycle (Part 22).

**Manual demotion is one Telegram command.** `/demote <scope>` drops a scope one level immediately. Trust is the owner's to grant and to revoke.

**Per-scope, not global.** Pricing might be at `act_alone` while hiring is still at `watch`. Each scope earns trust independently. A new scope (the owner just expanded into a new service line) starts back at `suggest` even if other scopes are mature.

### The four levels

1. **Watch** — the audit gate's verdict is logged but no action is taken. The Brain only observes.
2. **Suggest** — audit-approved actions arrive in Telegram as drafts. Owner replies with `1 Approve`, `2 Edit`, or `3 Discuss`.
3. **Act with approval** — audit-approved actions arrive in Telegram as one-tap messages. `1 Approve`, `2 Edit`, `3 Discuss`. Auto-expires after 4 hours waking / 12 hours overnight.
4. **Act alone** — audit-approved actions execute immediately. Owner sees them in the morning digest.

### Promotion criteria (all must be true)

The thresholds below apply during the 30-day onboarding sprint (Part 4). They are intentionally permissive to make the 30/80 target reachable. After day 30, the production thresholds raise.

**Sprint thresholds (days 0-30):**
- Minimum decision count in scope: **20**
- Average confidence on heuristics in scope: **> 0.7**
- Owner override rate: **< 10%**
- Owner explicit approval to move up

**Production thresholds (day 30+):**
- Minimum decision count in scope: **50**
- Average confidence on heuristics in scope: **> 0.8**
- Owner override rate: **< 5%**
- Owner explicit approval to move up

**Low-stakes auto-promotion.** A scope tagged `low_stakes: true` in the taxonomy can auto-promote (no owner approval click needed) once thresholds are met. The owner is notified in the morning digest. Examples: appointment confirmations, FAQ replies, calendar shuffles. High-stakes scopes (pricing, hiring, contracts) always require explicit owner approval to promote.

The first three are checked every night by Job 7 of the Sleep cycle (autonomy re-evaluation). The owner's explicit approval (when required) is the gate that turns a "ready for promotion" flag into an actual promotion.

### Demotion criteria (any one triggers automatic demotion)

- Override rate spikes above 15% in any 7-day window
- A non-negotiable violation slips through (drops to `watch`, not just one level)
- Owner edits more than 30% of approved actions in a 7-day window

These checks also run every night as Job 7 of the Sleep cycle. Demotion is immediate (no owner approval needed); the owner is notified next morning.

### Per-scope, not global

Pricing might be at `act alone`. Hiring might be at `watch`. Each scope earns trust independently.

---

## Part 16 — Logging the decision

### What gets stored

Every decision creates a row in the `decisions` table:

```
decision_id
event_id (which event triggered it)
scope, domain, decision_type
classification_confidence
salience_score
working_memory_used (yes/no)
retrieval_lanes_used (which lanes returned results)
heuristics_referenced (list of heuristic ids)
similar_decisions_referenced (list of decision ids)
foundation_files_used (list of yaml file paths)
system_1_answer
system_2_answer
divergence_score
proposed_action
audit_verdict
audit_reasoning
final_action (could be different from proposed if downgraded)
autonomy_level_at_time
state_band_at_time (green / yellow / red)
effective_level_at_time (after owner state gate modulation)
owner_action (if approval needed: approved, edited, rejected, expired)
created_at
```

### Why so much

Every column above is a signal we will use later for pattern detection, drift checks, calibration scoring, mentoring questions, and debugging.

### Embedding

For decisions with salience > 0.2, the situation + reasoning + outcome get embedded and stored in pgvector. Low-salience decisions skip embedding to save cost.

---

## Part 17 — Action layer and Telegram bot

### Three layers of owner interface

Everything the owner experiences from Solomon flows through Telegram. There is no web app for daily use. The bot serves three layers:

1. **Approval flow.** One-tap and suggestion messages. The training and approval phase mechanics. Covered in this Part.
2. **Conversation.** Free-form dialog any time. Owner asks, directs, brainstorms, vents. Solomon answers and learns. Covered in Part 18.
3. **Reports.** Daily, weekly, and on-demand reports. The reporting phase output. Covered in Part 19.

All three feed the same brain. A directive in conversation can become a heuristic. An edit on a one-tap can become a heuristic. A weekly report shows what changed.

### Two kinds of business action

Every approved action is one of:

1. **Outbound business action.** The brain executes against an external system (sends an email, books a calendar slot, posts to Slack, creates an invoice).
2. **Owner-facing message.** The brain sends a Telegram message asking the owner to ship, edit, or skip.

Both share the same logging path. Both count as "what the brain did today."

### Outbound business action types

- Send email (Gmail API)
- Send SMS (Twilio)
- Update CRM record
- Create or modify calendar event
- Post to Slack
- Send invoice (QuickBooks)
- Schedule a job (Jobber, Housecall Pro)

### The Telegram bot — the owner's only interface

The Telegram bot is how the owner experiences the brain. It is the only consumer-facing surface. Mentoring sessions, approvals, reports, and conversation all happen inside Telegram.

**Outbound message types:**

| Type | When | Format |
|---|---|---|
| One-tap suggestion | Audit-approved action at `act_with_approval` level | Action draft + `1 Approve  2 Edit  3 Discuss` |
| Suggestion-only | Audit-approved at `suggest` level, or downgraded | Action draft + `1 Approve  2 Edit  3 Discuss` |
| Escalation | Audit rejected, non-negotiable hit, or red-band high-stakes event | Full context + `Tell me what to do` (free-text reply) |
| Conversation reply | Solomon responding to a free-form owner message (Part 18) | Natural-language reply, optionally with `1 Save as rule  2 Don't save` if a heuristic candidate was detected |
| Daily report | 7am local | See Part 19 |
| Weekly report | Sunday or Monday morning | See Part 19 |
| Morning digest | 7am local (Phase 1-2 only; replaced by daily report when reporting phase activates for most scopes) | List of overnight act-alone actions, today's queue size, current state band |
| Evening recap | 9pm local | What shipped today, what's still pending, what was learned |
| Mentoring session | Scheduled cadence | Voice-note Q&A flow (see Part 21) |
| Promotion proposal | Job 7 flagged a scope ready | "Pricing is ready for act-with-approval. Approve?" |

**Inbound message handling:**

The bot routes inbound messages through a small classifier before doing anything else:

1. If the message is `1`, `2`, or `3` and a pending one-tap exists → approval handler. Updates `pending_approvals`, ships or edits or skips.
2. If the message is a slash command (`/vacation`, `/demote pricing`, `/force_normal`, `/report`, etc.) → command handler.
3. If a mentoring session is active → session runner.
4. Otherwise → conversation handler (Part 18).

Every inbound message becomes a `RawEvent` with `source = telegram_owner_inbound` for logging and learning, regardless of which handler processes it. Telegram messages reach Solomon as text. Users who prefer to speak rather than type use Wispr Flow or their phone's built-in voice-to-text on the Telegram app side; the bot itself only ever receives text.

**Edit flow.**
The owner taps `2 Edit`. The bot replies with the draft as editable text. The owner sends the corrected version. The corrected version is what ships and is logged as `owner_action: edited` along with the diff. Edits are a learning signal — the brain compares its draft to the owner's edit on the next sleep cycle and updates the relevant heuristic if a pattern emerges.

**One pending one-tap at a time per scope.**
The bot does not stack 12 approval messages on the owner. If a new one-tap in scope X arrives while one is still pending, the new one queues silently. The owner clears the current one first. Cross-scope, multiple messages can be pending. (This rule applies only to one-taps. Conversation messages and reports are not throttled.)

**Time-to-live.**
Pending one-tap messages auto-expire after 4 hours during waking hours, 12 hours overnight. Expired messages are not counted as overrides.

### Every action becomes a logged event

The action itself is captured as a new event with `source = system_action` or `source = telegram_message`. This way it shows up in the decision log just like inbound events.

### Action carries its predictions with it

When an outbound action goes out, its prediction checkpoints are scheduled. The prediction-checker job will look for matching outcomes at the right times.

### Module ownership

- `action/dispatcher.py` — routes audit-approved actions to outbound or telegram path
- `action/outbound/*.py` — one file per integration (gmail, twilio, slack, etc.)
- `telegram/bot.py` — Telegram bot connection and inbound classification
- `telegram/outbound.py` — formats outbound message types
- `telegram/approval_handler.py` — 1/2/3 replies on pending one-taps
- `telegram/command_handler.py` — slash commands
- `telegram/conversation.py` — Part 18 free-form dialog
- `telegram/reports.py` — Part 19 daily and weekly reports
- `telegram/digest.py` — morning and evening digest builders (Phase 1-2)

---

## Part 18 — Conversation mode

### What it is

Free-form dialog between the owner and Solomon, available at any time through the Telegram bot. Distinct from the approval flow. The owner can ask questions, give directives, share status, brainstorm, or vent. Solomon responds in natural language and captures the conversation as training data.

This is the part of the system that makes Solomon feel like a working partner instead of a notification service.

### Why it matters

Two reasons.

First, the owner cannot cover every rule in onboarding interviews. Most of how they think becomes visible only during the work — when they explain a decision to a colleague, when they react to a piece of news, when they think out loud. Conversation captures this. Without conversation, the brain only learns from taps and overrides, which is a narrow signal.

Second, in Phase 3 the owner is no longer tapping. Conversation is how they stay connected to the business: they ask Solomon what's happening, push back on something they read in a report, or hand it new context. Without conversation, the reporting phase is a one-way channel. With conversation, it stays a relationship.

### How a conversation starts

Two ways:

1. **The owner messages Solomon.** Free-form text in Telegram, any time. (We recommend Wispr Flow or phone voice-to-text for fast input, but Solomon only ever receives text.)
2. **The owner taps "3 Discuss" on a one-tap or suggestion.** This converts an approval moment into a dialog. Solomon opens the conversation by asking what concerns the owner about the proposed action. The original draft and full context stay in scope for the duration of the conversation. When the dialog ends — either with the owner saying to ship a (possibly revised) version, or saying not to act — the outcome is logged against the original decision and any extracted reasoning becomes a candidate heuristic for the next sleep cycle.

The "Discuss" path is the most valuable training signal in the whole system. It is the moment where the owner explains *why* the brain's draft was wrong. That reasoning is exactly what's missing from heuristics built only from tap and edit data.

### Message intents

When a free-form message lands in the conversation handler, Solomon classifies the intent first, then responds. Intents (one Claude call, structured output):

- **Question** — "What's happening on the Maple Street project?" "Why did you skip that quote yesterday?" "How are margins this month?"
- **Directive** — "From now on, always charge 35% premium on government work." "Don't ever take calls from this guy again."
- **Status update** — "Just signed the Henderson contract." "Mike is out sick today."
- **Brainstorm** — "I'm thinking about expanding into multi-family. What do you think?"
- **Vent / context** — "I'm fried today. Long day." "That McKenzie job is going to be a headache."
- **Mixed** — most real messages contain more than one. Solomon handles each part.

### How Solomon responds, by intent

**Question.** Solomon retrieves from working memory, long-term storage, recent decisions, and reports. Returns a concise answer with sources where useful. If the question is about a specific decision, links the decision id. If the question can be answered from a report, references it.

**Directive.** Solomon extracts the candidate heuristic, drafts it in standard form, and replies:
> "Got it. Saving as a rule: *Government work always charged at 35% premium minimum.* Scope: pricing/government. 1 Save  2 Edit the wording  3 Don't save"

If the directive contradicts an existing heuristic, Solomon flags the conflict and asks what to do.

**Status update.** Solomon captures the fact, updates working memory, and triggers any workflows that depend on it (e.g., "just signed Henderson" might create a project record). Responds with a short acknowledgment plus anything Solomon thinks is worth flagging:
> "Logged. Henderson is now active. Should I set up the kickoff workflow we used for Bridgewater?"

**Brainstorm.** Solomon engages. Pulls relevant context, offers reasoning, asks clarifying questions. Does not propose new heuristics from a brainstorm — those need to land as explicit directives. The whole conversation is captured for sleep-cycle review.

**Vent / context.** Solomon listens. Captures the emotional state as context. Does not try to solve it unless asked. May offer a short acknowledgment ("That sounds rough. Want me to handle the McKenzie quote draft tonight so it's off your plate?") or may just respond with a short reply.

### Learning from conversation

Every conversation message is a `RawEvent` and runs through the standard pipeline (salience → classify → retrieve → reason → log). What happens next depends on what was extracted:

- **Directive accepted** → heuristic created with `source: conversation`, `initial_confidence: 0.7` (high because explicit). Equivalent to mentoring-derived.
- **Directive declined** ("don't save") → still logged. If the same directive is declined twice, Solomon stops proposing it. If it's stated three times without being saved, Solomon escalates: "You've said this three times — should I save it now?"
- **Question with a corrective answer** — e.g., owner asks why a decision was made, Solomon explains, owner says "that's wrong, the actual reason should have been X" → goes into the next sleep cycle as a regret signal tied to the original decision.
- **Brainstorm conclusions** — if the brainstorm ends with a stated rule ("okay, so we're going to start doing X"), that becomes a directive (above). Otherwise the conversation is just captured.
- **Status updates** — update working memory, may create or update entity records.
- **Vent / context** — captured as state context, attached to the day's `state_band` log so the brain has more than just Whoop signals about how the owner was doing.

### Sleep cycle review of conversations

Job 3 (surprise replay) is extended in this version: it also pulls the day's high-salience conversations and looks for:
- Directives that were stated but not saved (heuristic candidates)
- Statements that contradict existing heuristics (conflict candidates)
- Statements that update the foundation (e.g., the owner expressed a new principle)

Anything found becomes a question for the next mentoring session.

### Latency expectations

Conversation responses use System 2 (Opus) reasoning by default but skip the audit gate (the gate is for outbound actions, not internal answers). Target response time: under 10 seconds for questions and directives, under 30 seconds for brainstorms that need deeper retrieval.

### What conversation is not

- **Not a chat companion.** Solomon does not initiate small talk, doesn't check in, doesn't ask how the owner's day is going. It only initiates when there's a real reason (an approval, a report, an escalation, a mentoring session, a heuristic conflict). The owner starts the conversations.
- **Not a search engine.** Questions get answered from the brain's actual knowledge — captured events, decisions, heuristics, foundation files. Solomon doesn't go search the web on behalf of the owner.
- **Not a memory dump.** Conversations are captured but the brain extracts what's useful and lets the rest decay normally. The full transcripts stay in `raw_events` for audit but are not reloaded as context for future decisions.

### Module ownership

- `telegram/conversation.py` — handler entry point
- `conversation/intent_classifier.py` — single Claude call to classify message intent
- `conversation/responders/question.py` — retrieval-and-answer flow
- `conversation/responders/directive.py` — heuristic candidate extraction and confirmation
- `conversation/responders/status.py` — fact capture and workflow triggers
- `conversation/responders/brainstorm.py` — extended dialog with retrieval
- `conversation/responders/vent.py` — listen-mode response
- `conversation/learning.py` — feeds extracted signals into the heuristic, foundation, and mentoring pipelines

---

## Part 19 — Reports

### What this is

The output of Phase 3. As scopes earn `act_alone` status, the owner stops seeing one-taps for them and starts seeing reports instead. Three report types: daily, weekly, on-demand.

Reports are not just lists. They are written by Claude (Opus) using the same retrieval and reasoning the brain uses for decisions. They explain what happened, why, what's working, what's not, and what was fixed.

### Daily report (7am local, Phase 3)

A short morning briefing covering the previous 24 hours. Replaces the morning digest for any scope at `act_alone`. (The morning digest still exists for scopes at `suggest` or `act_with_approval` — those need owner attention, not summary.)

Structure:

```
Yesterday in numbers
- 47 decisions, 41 shipped without asking, 4 one-taps (3 approved, 1 edited), 2 escalations
- Override rate: 2.4%. Edit rate: 8.5%. State band: green most of the day.

Notable
- Edited the Henderson follow-up (you changed the timing from "this week" to "Friday").
  This is the 3rd time you've moved a follow-up later. I'll propose updating the
  follow-up cadence rule in the next mentoring session.
- Escalated the Acme dispute. Still in your queue.
- The plumbing quote pattern from your operations rule fired twice. Both quotes
  came in 22% over expected. Same vendor. Worth noting.

Today's predicted shape
- Pricing scope expects 8-12 events (typical for Tuesdays).
- Two follow-ups you scheduled for today are queued.
- McKenzie project closeout is on the calendar. I have a draft punch-list ready
  if you want to review it.

State today
- Whoop: recovery 78, slept 7h12. Green band. Operating at full autonomy.
```

The report is generated by a daily job at 6:30am that pulls the previous 24 hours of decisions, runs Claude Opus to draft the report, and posts to Telegram at 7am.

### Weekly report (Sunday or Monday morning, owner's preference)

A deeper review covering the previous 7 days. Generated Sunday night.

Structure:

```
Week of <date> — Performance summary

Top line
- 312 decisions, 278 act-alone, 28 one-taps, 6 escalations
- Override rate: 3.1% (last week 4.2%, trending down)
- Edit rate: 7.8% (last week 7.1%, trending up slightly)

Per scope
- Pricing/commercial: act_alone, 64 decisions, 1.5% override. Healthy.
- Pricing/government: act_with_approval, 8 decisions, 0% override. Ready to
  promote to act_alone — proposal in your queue.
- Scheduling: act_alone, 89 decisions, 4.4% override. Slight uptick from
  rescheduling the Henderson timeline twice. Watch for next week.
- Vendor: suggest, 12 decisions, 33% override. You're rejecting a lot. The
  underlying rules may be off — this is queued for the next mentoring session.
- Hiring: watch (no actions).
- ... (one line per scope)

Issues hit this week
- 2 audit gate rejections (both pricing/government, both about non-standard terms)
- 4 prediction misses (3 in scheduling, 1 in pricing) — recovery quotes coming
  back later than expected
- 1 conflict between heuristics (after-hours pricing rule contradicted the
  loyalty discount rule on the Bridgewater quote)

Fixes applied this week
- Updated heuristic h_4889 (after-hours pricing) to v3 with size tier
- Promoted scheduling/recurring to act_alone
- Demoted vendor/new from act_with_approval back to suggest
- 6 new heuristics from your conversations and edits

What I'd like your attention on
- The vendor/new override rate is the strongest signal this week. The mentoring
  session next Tuesday has 4 questions queued about it.
- Scheduling timeline drift — three of the four prediction misses were the same
  pattern. May need a new heuristic.
```

### On-demand reports

The owner asks in conversation. Solomon retrieves and writes.

Examples:

- "How's the McKenzie deal going?" → project report (status, recent decisions, predictions outstanding, anything stuck)
- "Show me everything I overrode this week" → review report (each override with the brain's draft and the owner's edit, grouped by scope)
- "Why did pricing/government demote?" → diagnostic report (the override pattern, the heuristics involved, what changed)
- "What rules am I most likely to want to update?" → mentoring preview (the questions queued for the next session)

These are routed through Part 18 conversation as questions, with the responder generating a report-formatted answer when the question warrants one.

### Issues and fixes — what counts

The "issues" and "fixes" sections of the daily and weekly reports are populated automatically. Definitions:

**Issue events:**
- Audit gate verdict was REJECT
- Prediction was marked MISSED
- Heuristic was downgraded to FRAGILE
- Two heuristics conflicted in the same decision (Sleep cycle Job 5)
- A regret signal accumulated past threshold
- A scope was demoted
- Override rate or edit rate exceeded their thresholds in any 7-day window

**Fix events:**
- Heuristic version bumped (with provenance)
- Heuristic un-archived because semantic retrieval surfaced it correctly
- Foundation YAML committed (any file)
- Autonomy promoted on a scope
- New heuristic created from conversation, edit pattern, or surprise replay
- Pending heuristic accepted into the active set

Both lists are aggregated by Job 7+ at the end of the sleep cycle and stored in a `report_signals` table for the report generators to pull from.

### When the reporting phase activates

There is no global switch. Each scope individually moves into the reporting phase when it reaches `act_alone`. A scope at `act_alone` shows up in the daily report's numbers and notable sections. A scope at `act_with_approval` still produces one-tap messages and is summarized in the daily report's pending section. A scope at `suggest` produces draft messages and is mentioned only when something noteworthy happens.

By Phase 3, most scopes are act_alone, the daily report covers most of the work, and one-taps are rare.

### Module ownership

- `reports/daily.py` — daily report generator (runs 6:30am)
- `reports/weekly.py` — weekly report generator (runs Sunday night)
- `reports/on_demand.py` — handlers for in-conversation report requests
- `reports/issue_detector.py` — populates issue events from decision and prediction logs
- `reports/fix_detector.py` — populates fix events from heuristic, foundation, and autonomy logs
- `reports/templates/` — Claude prompts for each report type

---

## Part 20 — Predictions and counterfactuals

### Predictions

Every action that goes out includes one or more checkpoint predictions:

```
prediction_id
decision_id (which decision made this prediction)
prediction_text (what we expect to happen)
expected_by (datetime)
status (pending, met, missed, partial)
actual_outcome (filled in later)
checked_at (when the system looked for the outcome)
```

### How predictions get checked

A scheduled job runs every hour. Pulls all `pending` predictions whose `expected_by` is past. For each one:

1. Searches Capture and Storage for events that might be the outcome.
2. If found, asks Claude: "Does this outcome match the prediction?"
3. Updates `status` to `met`, `missed`, or `partial`.
4. The result feeds into confidence scoring and the next pattern engine run.

### Counterfactuals

For every important decision (salience > 0.4), the Orchestrator also generates:

```
counterfactual_id
decision_id
alternative_choice (what we did NOT do)
predicted_outcome_for_alternative (what we expected if we had)
```

When the actual outcome arrives, both the chosen path and the alternative get evaluated. If the alternative would have been better, that's a strong signal to update the heuristic.

### Why this matters

Without predictions, the brain only learns from outcomes — and outcomes are slow and noisy. With predictions, the brain learns from calibration: was my forecast right? Calibration improves much faster than outcome-only learning.

---

## Part 21 — Mentoring sessions

### What they are

Scheduled sit-downs where the Conductor (using Claude) asks the owner targeted questions. Outputs become new heuristics, foundation updates, or skill playbooks.

### Two kinds of mentoring

There are two distinct types of mentoring, and both run through the same Telegram conversation flow but trigger differently and target different gaps.

**1. Reactive mentoring.** Triggered by something that happened — a confusing decision, a heuristic conflict, a high override rate in a scope, a regret signal. The questions are tied to specific events. The goal is to resolve real ambiguity the brain hit during the day or week. This was the only mentoring type in the original spec.

**2. Proactive training mentoring.** Solomon initiates this. The goal is for Solomon to fill gaps in its own understanding *before* a real situation tests it. Solomon does its own gap analysis, generates fresh questions tailored to the user's specific industry and the agentic functions Solomon is currently managing, and asks them. This is the type that lets Solomon get ahead of its blind spots instead of always playing catch-up.

The two types share infrastructure (the `mentoring_sessions` table, the question-asking flow, the foundation-update flow) but differ in how questions are generated and when sessions are scheduled.

### How proactive training mentoring works

Before each training session, Solomon runs an internal research pass. It reads:

- Every foundation YAML (industry profile, beliefs, why, principles, ideal outcomes, non-negotiables, taxonomy)
- Every active heuristic and its coverage map (which scopes have many rules, which have few)
- The decision log since the last training session (or since onboarding ended, if first training)
- The surprise log
- The conflict log
- All previously asked questions (from `onboarding_sessions` and `mentoring_sessions` transcripts) — for dedup

Then it identifies gaps. A gap is anywhere Solomon *might* face a decision and lacks the rule, principle, or example to make it confidently. Gaps come in several flavors:

- **Untested scope coverage.** Solomon has been managing pricing and scheduling but has never made a hiring decision. What are the user's hiring rules?
- **Edge cases of existing rules.** Solomon has the rule "pay above market for 3+ year tenants." What about a tenant at 2.9 years? What about a tenant who was great for 4 years and then started to slip?
- **Counterfactuals on real recent events.** A vendor paid on time last week. What if they hadn't? What if they paid late three times in a row? At what point would the user fire them?
- **Philosophical and moral.** Where is the line between firm and harsh? When does loyalty stop being a virtue and start being a liability? What does the user owe a long-term employee in a downturn?
- **Industry-specific edge cases.** For a flipper: what if the inspection comes back with a foundation issue mid-deal? For a landlord: what if a tenant's child gets seriously ill and they can't pay?

The output of the research pass is a candidate question list, deduped against everything ever asked, prioritized by which gap is most likely to be tested by real events soon.

### When training sessions are scheduled

Solomon proposes training sessions to the user via Telegram. The user accepts or reschedules.

The cadence is dynamic and inversely tied to how much guidance Solomon has needed lately. The fewer overrides, edits, and escalations Solomon has had, the less it needs training, so sessions get less frequent over time. The opposite is true if guidance has spiked.

**The cadence formula.**

A `training_pressure` score is computed nightly during the sleep cycle. It is a weighted sum of:

- Override rate in the last 7 days (overrides per 100 decisions)
- Edit rate in the last 7 days (edits per 100 decisions)
- Escalations per day in the last 7 days (audit rejects, non-negotiable hits, Discuss-button taps)
- Surprise rate (high-divergence events per day in the last 7 days)
- Days since last training session

The pressure score maps to a cadence:

- Pressure HIGH → propose a training session this week
- Pressure MODERATE → propose a session in 2-3 weeks
- Pressure LOW → propose a session in 4-6 weeks
- Pressure VERY LOW → propose only when the user requests one (`/train`)

This means: as Solomon needs less and less guidance because more decisions are covered, training sessions naturally space out. As the brain matures, training becomes rare. At full maturity (Phase 3), training sessions might happen quarterly or only when the user adds a new business line.

Reactive mentoring (the original kind) runs on its own schedule based on accumulated reactive triggers (surprise log buildup, conflict count, override threshold breaches). Reactive sessions can happen weekly during early Phase 1 even when training pressure is low, because real events are still teaching the brain a lot.

### How sessions are proposed

Solomon sends a Telegram message:

> I have ~7 questions queued for a training session. Topics: hiring decisions, edge cases on the after-hours pricing rule, two philosophical questions about tenant relationships. Estimated time: 15-20 minutes. When works?
>
> [ Now ]   [ Today later ]   [ Pick a time ]   [ Skip this one ]

The user picks a slot. Solomon adds it to the calendar (via the calendar integration). At the scheduled time, Solomon opens the session in Telegram.

### Caps and protections against the question treadmill

- Maximum 10 questions per session.
- Maximum 1 training session offered per week (the user can request more with `/train` but Solomon does not propose more than once a week).
- No training sessions during the first 30-day onboarding sprint. The 6 foundation interviews are doing this work; doubling up would burn out the user.
- If the user skips a proposed training session, Solomon does not re-propose for at least a week.
- If the user has skipped 3 proposed training sessions in a row, Solomon stops proposing for a month and writes a note for the next reactive mentoring session ("the user has been declining training; ask in the next reactive session whether we should change the cadence").

### Three kinds of question gaps

Maintained from the original spec, these inform both reactive and training mentoring:

1. **Coverage gaps** — "I have no heuristic for X. How would you handle it?"
2. **Confidence gaps** — "I have a heuristic for Y but it's contradicted itself. Which is right?"
3. **Drift gaps** — "I haven't tested heuristic Z in 90 days. Is it still right?"

Plus three question types:

- **Scenario-based** — "Walk me through how you'd handle this situation."
- **Hypothetical** — "What if it had gone differently?" (heavy in training mentoring)
- **Philosophical** — "Where is the line between X and Y?" (heavy in training mentoring)

### How questions get prioritized

By:

- Volume (how many decisions touched this gap?)
- Salience (how important were those decisions?)
- Surprise (how often did the brain get surprised in this gap?)
- Industry relevance (training questions weight industry-specific gaps higher)
- Recency of the most recent related event (asking about a vendor right after a vendor incident is more useful than asking about hiring six months later)

Top 5-10 questions per session, time-budgeted to fit the owner's available slot.

### Where answers go

Both reactive and training mentoring write to the same destinations:

- Scenario and hypothetical answers → new or updated heuristics in the `heuristics` table
- Philosophical answers → updates to `principles.yaml` or `non_negotiables.yaml`
- Multi-step answers → entries in the `user_skills` table (as playbooks)
- Industry-specific answers → updates to `industry_module_questions.yaml` and new heuristics
- The full session transcript → `mentoring_sessions` table (with session_type=`reactive` or `training`)

Additionally, training sessions write to a dedicated `training_signals` table — see below.

Every answer is versioned. Old answers are archived, not deleted. The owner can change their mind without losing the history.

### The `training_signals` table

A dedicated record of what proactive training has produced. Different from `mentoring_sessions` (which captures the conversation) and from `heuristics` (which captures the rule). `training_signals` captures the *gap* and the *fill*.

Each row:
- The question asked
- The gap type (coverage, confidence, drift, philosophical, hypothetical)
- The scope and domain it targeted
- The user's answer
- What was created or updated as a result (heuristic IDs, foundation file paths, user_skill IDs)
- The session_id it came from
- A semantic embedding of the question (for future dedup)

This table is what lets Solomon say "I haven't asked about hiring before" or "we covered tenant moral edge cases in March, but not contractor moral edge cases." It is the answer to your question about a clear place where training is stored.

### How dedup works

Before adding a question to a training session's queue, the question generator does a semantic search against `training_signals.question_embedding` (and against past mentoring transcripts via the embeddings index). If a sufficiently similar question has been asked before, it is skipped. If a related-but-not-identical question has been asked, the new question references the prior answer ("you said X about Y; what about Z?") so the brain builds knowledge by extension rather than by repeating.

---

## Part 22 — Sleep cycle (nightly jobs)

### What it is

A scheduled set of jobs that runs every night between 2am and 5am local time. The brain consolidates while the owner sleeps. **This is where refinement actually happens.** The day-time pipeline (capture, reason, audit, act) is the brain doing its job; the night-time pipeline is the brain getting better at its job. Without these jobs, the brain would be a fixed set of rules forever. With them, the rules grow, sharpen, fade, and adapt every night.

Each of the eight jobs mirrors something the human brain does during sleep or rest. Together they form the system's self-improvement engine.

### Cycle-level rules

These apply to every job in the cycle.

- **Order matters.** Jobs run sequentially from Job 1 to Job 8 in the order listed below. Each later job can use signals that earlier jobs produced. (Counterfactual results inform surprise replay; surprise / fragility / conflict / regret / autonomy signals all feed the mentoring scheduler at the very end.)
- **Per-job error handling.** Each job runs inside its own try/catch. If one job throws, the cycle logs the failure and continues with the next job. Never let one bad job kill the whole cycle.
- **Token budget per user per night.** Every Claude call debits the budget. If the budget is exhausted mid-cycle, the remaining jobs skip LLM calls and run in rule-only mode (no surprise replay LLM calls, no stress-test LLM calls). Costs are bounded; the cycle always finishes.
- **End-of-cycle log.** A `cycle_log` row gets written at the end with start_time, end_time, total tokens spent, items processed per job, and per-job status (success / fail / skipped). The owner sees a morning digest summarizing the night.
- **Designed to become a Conductor skill.** The logic in each job is structured as plain if-else prose so it can be lifted into a `sleep_cycle/` skill module the Conductor calls.

### Job 1 — Hindsight check

**What this mirrors in the brain.** When you replay the day at bedtime and think "I should have done X instead," that's hindsight — looking at past decisions with new information (the actual outcome) and asking whether the OTHER choice would have been better. This is how humans learn from regret without repeating the mistake.

**What we want from it.** Sharper calibration over time. The brain learns when its choices led to worse outcomes than the alternative would have, and updates the rules that drove those choices. Predictions get more accurate. Regret becomes a learning signal, not just a feeling.

The Conductor queries the `predictions` table for predictions whose `expected_by` date has passed but have no recorded `outcome`.

For each such prediction:
1. Search captured events from `action_time` to `expected_by + 24h` for an event matching the predicted outcome.
2. If a matching event is found:
   - Update calibration metrics for the chosen-path prediction (record actual vs. expected error).
   - Compare the actual outcome to the alternative-path prediction.
   - If the alternative path would have produced a better outcome, write a `regret_signal` row tagged with the heuristic that drove the original choice and a `failure_layer` field (one of: `heuristic`, `audit_gate`, `autonomy_level`, `action_layer`).
   - If a heuristic accumulates ≥3 `regret_signals` in 60 days, set its `mentoring_priority = "regret_pattern"`.
3. Else if no matching event AND `expected_by + 30 days` has passed:
   - Mark the prediction as `unresolved`. Counts as a calibration miss.
4. Else: leave the prediction open. Try again tomorrow.

### Job 2 — Rule archival

**What this mirrors in the brain.** The brain shifts rarely-used knowledge out of active recall into long-term memory. It's still there. You can still pull it back when something reminds you of it. It just doesn't take up active attention.

**What we want from it.** The active rule set stays small enough that retrieval is fast and prompts don't bloat. Rules that aren't currently relevant get moved out of the hot set but stay searchable in semantic retrieval — when a relevant situation comes back, the brain finds them again. No knowledge is ever lost.

For every heuristic in the `heuristics` table:

1. Compute `days_since_last_use = today − last_used_date`.
2. If `days_since_last_use ≤ 90`: leave the heuristic `active`.
3. Otherwise: set `status = "archived"`. Archived heuristics stay in storage and remain searchable via semantic retrieval (Part 11). They are filtered out of "active set" queries that pre-load hot rules into the System 1 prompt, but they are not filtered out of vector similarity search. If the situation recurs, retrieval will surface them.

**Un-archival on use.** When the day-time retrieval pipeline (Part 11) pulls an archived heuristic into a decision context (via the semantic lane) and the resulting decision actually references it (`heuristics_referenced` includes its ID), the Conductor sets `status = "active"` and updates `last_used_date`. The next nightly cycle treats it as fresh.

**This job does not touch `confidence`.** Confidence is updated by other mechanisms — override penalty, prediction met/miss, stress-test failure (Part 23 "How confidence changes"). Time-based decay is removed. Rules now lose confidence only on *evidence*, not on the calendar.

### Job 3 — Surprise replay

**What this mirrors in the brain.** During REM sleep, the brain replays the day's most surprising moments — not the routine ones. Surprises are signals that the existing rules didn't fully cover the situation, and new long-term memories form from these moments more than from anything else.

**What we want from it.** New rules come from genuine gaps in coverage, not from noise. When the brain is repeatedly surprised in the same way, it proposes a new rule to handle that pattern going forward.

1. Query yesterday's decisions sorted by `divergence_score` descending.
2. If yesterday's decision count `< 5`, skip this job.
3. Take the top 10.
4. Drop any with `salience_score < 0.3` (low-importance surprises are not worth learning from at LLM cost).
5. Group the remaining decisions by similarity (same scope + similar pattern). Call this the cluster set.

For each cluster:
1. Look in `pending_heuristics` for an existing entry with the same scope and similar pattern.
   - If found: increment its `support_count`, append cluster decision_ids to its `evidence_list`. Skip to next cluster.
2. Otherwise, send a representative decision to Claude (Opus) with the prompt: *"Given everything we now know, what should we have done? What heuristic was missing? Return one of: NO_NEW_HEURISTIC, NEW_HEURISTIC, or UPDATE_EXISTING."*
3. Branch on Claude's response:
   - `NO_NEW_HEURISTIC`: do nothing.
   - `NEW_HEURISTIC`: write to `pending_heuristics` with starting confidence `0.5`, `support_count = cluster_size`.
   - `UPDATE_EXISTING (heuristic_id, new_version)`: write to `pending_heuristic_updates`.

Nothing in pending auto-promotes. Owner approves in mentoring.

### Job 4 — Stress test

**What this mirrors in the brain.** Imagining "what if this had been different?" — running a mental simulation under altered conditions. The brain uses this to check whether a rule it learned is general (covers many situations) or fragile (only worked because of one specific detail).

**What we want from it.** Rules that hold up under variation are trusted more. Rules that break when the situation changes get marked fragile. The brain stops over-applying rules it learned by coincidence.

1. Pick 5 decisions from the last 30 days. **Bias selection** toward decisions whose heuristics have not been stress-tested in the last 30 days (`last_stress_test < today − 30`).

For each picked decision:
1. Look up the scope's `mutation_library` — a per-scope structured list of mutation types.
   - Pricing scope: `amount × 2`, `amount × 0.5`, `time-pressure-flip`, `client-size-change`.
   - Hiring scope: `tenure-flip`, `role-seniority-flip`, `market-rate-change`.
   - Scheduling scope: `urgency-flip`, `weekday/weekend-flip`.
2. Pick one mutation at random. Apply it to the original context.
3. Send the mutated context to Claude (Sonnet — bulk testing, speed > depth) with the prompt: *"Same heuristics as before. With this new context, what would you do?"*
4. Claude returns an action.
5. If `new_action == original_action`: heuristic survived the mutation. Do nothing.
6. Else:
   - Write a `fragility_log` row (heuristic_id, mutation, new_action).
   - If this heuristic has ≥3 `fragility_log` rows in the last 90 days, mark it as `fragile` in the heuristics table.

Fragile heuristics still fire but get a `0.7` multiplier in retrieval scoring.

### Job 5 — Conflict detection

**What this mirrors in the brain.** Cognitive dissonance — the discomfort the brain feels when two beliefs or rules contradict each other. The brain pushes for resolution: ranking them, merging them, or rejecting the weaker one.

**What we want from it.** An internally consistent rule set. The brain doesn't flip-flop between contradictory rules across similar decisions. Clear conflicts get auto-resolved on the spot; genuinely ambiguous ones reach the owner.

Scan yesterday's decisions for cases where two heuristics in the same decision gave opposing advice (one said do X, one said do not X).

For each conflicting pair:
1. Read both heuristics' confidence values.
2. If one `confidence > 0.8` AND the other `confidence < 0.4`:
   - Auto-resolve. Keep the high-confidence heuristic. Archive the low-confidence one.
   - Write an `auto_resolution_log` row.
3. Else (similar confidences, true ambiguity):
   - Flag both heuristics as `in_conflict`.
   - If a heuristic accumulates ≥2 `in_conflict` flags in 30 days, write a `conflict_review` row and queue both heuristics for the next mentoring session.

### Job 6 — Working memory cleanup

**What this mirrors in the brain.** Working memory has limited capacity. The brain drops items that aren't being actively used so it can stay focused on what matters now. This is prioritization, not forgetting — anything important is already in long-term memory.

**What we want from it.** The short-term cache stays small and fast. The brain doesn't drag yesterday's irrelevant context into today's decisions, but doesn't lose anything still active either.

1. If the user is in `vacation_mode`, set `TTL = 14 days`. Else `TTL = 7 days`.

For every item in working memory (Redis):
1. `days_since_last_touch = today − last_accessed_date`.
2. If `days_since_last_touch < TTL`: keep.
3. Else check `open_items` table:
   - If item is tied to an open thread: keep (open threads override TTL).
   - Else evict.
4. After eviction, if cache size > 50 (the cap): evict lowest-salience-oldest items until size = 50.

### Job 7 — Autonomy re-evaluation

**What this mirrors in the brain.** Self-awareness of competence. You know which tasks you can do on autopilot and which you still need help with. This sense gets updated as you accumulate experience — graduating to doing things on your own as you prove you can, scaling back when you start making mistakes.

**What we want from it.** Autonomy reflects actual competence per scope. The brain doesn't act unilaterally where it shouldn't, and doesn't keep asking permission where it has earned trust.

For every scope in `autonomy_state`:

1. **Hysteresis check.** If this scope was promoted or demoted within the last 14 days, skip both checks for this scope and continue. (Prevents oscillation.)

2. **Compute trailing 30-day metrics:** `decision_count_30d`, `override_rate_30d`, `avg_confidence_30d`.
   **Compute trailing 7-day metrics:** `override_rate_7d`, `edit_rate_7d`, `non_negotiable_violations_7d`.

3. **Demotion check** (always runs, except if `current_level == watch`):
   - If `non_negotiable_violations_7d > 0`: demote scope to `watch` (drops all the way down). Write `incident_log` row. Notify owner **same night**.
   - Else if `override_rate_7d > 0.15`: demote one level. Notify next morning.
   - Else if `edit_rate_7d > 0.30`: demote one level. Notify next morning.

4. **Promotion check** (only if `current_level < act_alone` AND no demotion fired this night for this scope):
   - If `decision_count_30d ≥ 50` AND `override_rate_30d < 0.05` AND `avg_confidence_30d > 0.8`:
     - Flag the scope as `ready_for_promotion`.
     - Add a row to the owner's morning review queue: *"Pricing is ready for promotion to `act_with_approval` — review and approve?"*
     - Do NOT auto-promote. Owner approves with one click.

This job makes the autonomy ladder a living mechanism rather than a static config setting.

### Job 8 — Mentoring scheduler (runs last because it consumes signals from Jobs 1, 3, 4, 5, and 7)

**What this mirrors in the brain.** Recognizing when you need to ask for help. Knowing the difference between "I can figure this out" and "I should consult my mentor before I make this mistake again." Scheduling check-ins based on accumulated questions, not on a fixed calendar.

**What we want from it.** Mentoring time gets used efficiently. Both reactive sessions (responding to real events) and training sessions (proactive gap-filling) get scheduled at the right cadence. Questions with the highest learning value get prioritized.

This job runs two parallel scheduling decisions: reactive scheduling and training scheduling.

**Reactive scheduling.** Gather:
- `regret_pattern_flags_60d` (from Job 1)
- `new_pending_heuristics_7d` (from Job 3)
- `newly_fragile_heuristics_7d` (from Job 4)
- `new_conflicts_7d` (from Job 5)
- `ready_for_promotion_scopes` (from Job 7)
- `newly_demoted_scopes` (from Job 7)

If **any** of these conditions is true, a reactive session is urgent:
- `new_pending_heuristics_7d > 5`
- `newly_fragile_heuristics_7d > 3`
- `new_conflicts_7d > 2`
- `regret_pattern_flags_60d > 5`
- `ready_for_promotion_scopes > 0`
- `newly_demoted_scopes > 0`

Then propose moving the next reactive mentoring session within 7 days. Write a notification: *"I've accumulated N new questions and M scopes to review. Can we meet sooner?"*

Else stay on the current reactive cadence.

**Training scheduling.** Compute the training pressure score (Part 21):

- `override_rate_7d` (overrides per 100 decisions in last 7 days)
- `edit_rate_7d` (edits per 100 decisions)
- `escalations_per_day_7d` (audit rejects, non-negotiable hits, Discuss-button taps per day)
- `surprise_rate_7d` (high-divergence events per day)
- `days_since_last_training_session`

Map to a pressure band:
- HIGH → propose a training session this week
- MODERATE → propose a session in 2-3 weeks
- LOW → propose a session in 4-6 weeks
- VERY LOW → do not propose; only run if user requests via `/train`

Write the result to `training_pressure_log`. If a proposal is warranted AND the caps allow it (no proposal in last 7 days, not in 30-day onboarding sprint, user hasn't declined 3 in a row), the `mentoring-training-scheduler` skill is invoked to send the proposal via Telegram.

**Why both can fire on the same night.** Reactive and training mentoring target different gaps. A user might have a busy week with several conflicts (reactive triggers) and also be due for a routine training session. The two are scheduled separately and the user can decline one and accept the other.

The Conductor never auto-schedules. The owner picks the time for any session. The Conductor only proposes.

### Why all this at night

Each job is compute-intensive. Running them at night avoids slowing down the daytime decision pipeline. Mirrors the biological pattern: encode during the day, consolidate at night.

### Future improvements (not yet in scope)

- **Parallelize Claude calls** within Jobs 3 and 4 (surprise replay and stress test) — 5 in parallel batches instead of sequential.
- **Incremental processing** for Jobs 2 and 7 (only re-process scopes/heuristics with new activity since last cycle, not all of them).
- **Idempotency markers** on each `job_run` row so the cycle can resume safely after interruption.

---

## Part 23 — Heuristic lifecycle

This part pulls together everything about how heuristics get born, grow, change, and retire. It is the single source of truth for the refinement logic. When we build, this is the part to read first if we are touching anything related to heuristics.

### How a heuristic is born

Three paths into existence:

**Path 1 — Direct from mentoring.** The owner answers a scenario question. The brain extracts a rule and writes it as a heuristic. Initial confidence: 0.6. Source: `mentoring`. Provenance: the session id.

**Path 2 — Pattern engine extraction.** The pattern engine notices the same kind of decision repeated 5+ times with consistent reasoning. It proposes a heuristic. The proposal sits in `pending_heuristics` until owner reviews at next mentoring session. If approved: initial confidence 0.5. Source: `pattern_engine`. Provenance: list of decision ids that support it.

**Path 3 — Onboarding & ingestion seeding.** During onboarding, Claude reads the owner's session transcripts after Session 6 and proposes initial heuristics from things the owner stated directly (Source: `onboarding`, initial confidence 0.7 — higher because explicitly affirmed). The bulk-ingestion pipeline (Part 25) mines additional heuristic candidates from historical documents and queues them for owner review (Source: `ingestion`, initial confidence 0.5 — lower because inferred from behavior, not directly affirmed). Both flow through the same owner-approval gate before activation.

Every new heuristic is created with:
```
confidence: <initial>
status: active
version: 1
superseded_by: null
last_used_at: null
last_retrieved_at: created_at
last_updated_at: created_at
```

### How confidence changes

There are five ways confidence moves. They run at different times.

**Increment on successful use** — runs immediately after a decision closes successfully (no override, no complaint, prediction met or no prediction).

```
new_confidence = old_confidence + 0.02 * (1 - old_confidence)
```

The shape: confidence rises fast at first, slow near the top. A heuristic at 0.5 jumps to 0.51 per success. One at 0.95 only moves to 0.951. You can never reach 1.0.

**Decrement on owner override** — runs immediately when the owner edits, rejects, or contradicts an audit-approved action.

```
new_confidence = old_confidence * 0.85
```

Multiplicative. One override hurts more than one success helps. A heuristic at 0.90 drops to 0.765 in one override.

**Disuse handling** — runs nightly during Sleep cycle Job 2. For every active heuristic with `days_since_last_use > 90`, set `status = "archived"`. Archived heuristics stay in storage and remain searchable via semantic retrieval. When semantic retrieval pulls an archived heuristic into a decision and the decision references it, the heuristic is un-archived (`status = "active"`, `last_used_date = today`).

**Disuse does not change confidence.** A rule's age does not lower its confidence — only its track record does. Confidence is reserved for evidence-based signals (overrides, prediction outcomes, stress-test failures). This means a rare-but-correct rule (e.g., one that fires only during year-end audits) keeps its confidence intact during the off-season; it simply moves to the archived set and gets pulled back when relevant.

**Penalty on prediction miss** — runs when a prediction tied to a decision using this heuristic is marked `missed`.

```
new_confidence = old_confidence * 0.92
```

Mild. A miss might be noise. Multiple misses compound.

**Reward on prediction met** — runs when a prediction is marked `met`.

```
new_confidence = old_confidence + 0.03 * (1 - old_confidence)
```

Slightly stronger than a generic success because predictions test the brain's calibration directly.

### Status transitions

A heuristic is in one of four states. Movement is automatic except where noted.

```
ACTIVE → FRAGILE
  Trigger: stress test failure (Sleep cycle Job 4) OR
           owner override rate > 30% in last 30 days OR
           regret signal accumulated > 3 times in last 60 days
  Effect:  confidence multiplier of 0.7 applied at retrieval time
           heuristic gets extra weight in next mentoring session

FRAGILE → ACTIVE
  Trigger: owner confirms heuristic at mentoring session
  Effect:  status reset, confidence boosted by +0.1

ACTIVE → ARCHIVED
  Trigger: no use in last 90 days (Sleep cycle Job 2)
  Effect:  removed from the active "hot" rule set that pre-loads into
           System 1 prompts. Stays in the database. Still searchable
           via semantic retrieval (vector similarity) — if a decision
           context is similar enough, retrieval will surface it.
  Note:    confidence is NOT touched. A rare-but-correct rule keeps
           its confidence intact while archived.

ARCHIVED → ACTIVE
  Trigger: semantic retrieval pulls the heuristic into a decision AND
           the decision references it (heuristics_referenced includes
           its ID), OR owner explicitly reactivates at mentoring.
  Effect:  status flips to active, last_used_date updates to today.
           No confidence reset — the rule resumes with whatever
           confidence it had when archived.

ACTIVE → SUPERSEDED
  Trigger: owner approves a new version that replaces this one
  Effect:  superseded_by points to new heuristic id
           kept in database for audit
           never retrieved again
```

### Versioning

Heuristics are immutable once written. Updates create a new version, not an in-place edit.

When the owner approves an update:

1. Old heuristic gets `status = superseded`, `superseded_by = <new_id>`
2. New heuristic is created with `version = old.version + 1`
3. New heuristic inherits `provenance` from old, plus the mentoring session id where the update was made
4. Initial confidence of new version: 0.7 (higher than birth, because owner-validated, but not maxed because untested)

The full version chain is queryable: "show me how the after-hours pricing heuristic evolved over time" returns v1 → v2 → v3 → v4.

### What triggers a mentoring question about a heuristic

Five triggers. The mentoring question generator (Sleep cycle Job 8 + scheduled mentoring prep) checks these every time it builds a session:

**1. Drift trigger.** Heuristic hasn't been retrieved in 60 days. Question: "We haven't tested this rule lately. Is it still right?"

**2. Fragility trigger.** Status is `fragile`. Question: "This rule has been contradicted. Here are the cases where it failed. How should we update it?"

**3. Override trigger.** Override rate > 20% in last 30 days. Question: "You've been overriding this rule a lot. Walk me through what changed."

**4. Regret trigger.** Counterfactual evaluations show alternative would have been better 3+ times in 60 days. Question: "Recent decisions suggest the rule may be too conservative/aggressive. Update?"

**5. Conflict trigger.** Two heuristics gave opposing advice in the same situation. Sleep cycle Job 5 catches this. Question: "These two rules contradicted each other on this decision. Which is correct?"

Question priority is computed as:
```
priority = volume * salience * (1 + surprise_factor)
```

Where:
- `volume` = number of decisions affected
- `salience` = average salience of those decisions
- `surprise_factor` = average divergence score on affected decisions

Top 10-30 questions ship in the next session.

### The owner's view of a proposed update

When a proposed update reaches the mentoring session, the owner sees:

```
Heuristic: "After-hours commercial cleaning adds 20% premium"
Status: fragile
Reason for review: contradicted 4 times in last 14 days
Trigger: regret signal

Recent contradictions:
- Decision #4471 (Mar 12) — quoted Acme Corp at 35% premium, accepted
- Decision #4623 (Mar 18) — quoted Bridge Realty at 30% premium, accepted
- Decision #4701 (Mar 21) — quoted DataCo at 40% premium, accepted
- Decision #4812 (Mar 26) — quoted GovBuilding at 50% premium, accepted

Proposed update (drafted by the brain):
"After-hours commercial cleaning adds:
  - 20% for buildings under 10,000 sq ft
  - 35% for buildings 10,000-25,000 sq ft
  - 50% for buildings over 25,000 sq ft or government"

Your options:
[ Approve as drafted ]
[ Edit and approve ]
[ Reject — keep existing rule ]
[ Reject — archive entire rule ]
[ Defer to next session ]
```

The owner can also write free-text reasoning that gets stored with the new version. This becomes part of the heuristic's provenance.

### Retrieval-time scoring

When the Orchestrator pulls heuristics for a decision, the score for each candidate is:

```
final_score = lane_score
              * confidence
              * status_multiplier
              * recency_factor

status_multiplier:
  active = 1.0
  fragile = 0.7
  archived = 0.0 (excluded by default)
  superseded = 0.0 (excluded always)

recency_factor = exp(-0.005 * days_since_last_retrieved)
```

This means a high-confidence active heuristic recently used dominates. A fragile one with low recent use rarely makes the cut. An archived one is invisible unless explicitly searched.

### The full lifecycle, told as a story

Here is how heuristic h_4471 evolves over a year, with the actual mechanics shown:

**Day 1 — Mentoring session 1.**
Owner answers scenario about after-hours pricing. Heuristic h_4471 is born.
- `confidence: 0.6, status: active, version: 1`

**Days 2-60.**
Used 28 times. All approved without edits. 24 successful predictions met.
- 24 successes × +0.02 * (1 - confidence) = climbs from 0.6 to 0.84
- `confidence: 0.84, status: active, version: 1`

**Day 73.**
Owner overrides on Acme Corp quote (35% premium charged instead of 20%).
- `confidence: 0.84 * 0.85 = 0.714`

**Day 79.**
Owner overrides on Bridge Realty (30% instead of 20%).
- `confidence: 0.714 * 0.85 = 0.607`

**Day 80 — Sleep cycle Job 4.**
Stress test mutates context: changes "office" to "warehouse" and "small" to "large." h_4471 fails the mutation test.
- `status: fragile`
- Override trigger fires: 2 overrides in 7 days = override rate spike
- Question added to mentoring queue with high priority

**Day 80 — Sleep cycle Job 3.**
Surprise replay catches the Bridge Realty decision: System 1 said 20% (using h_4471), System 2 reasoned 30% (because it noticed building size). Divergence: 0.7. Logged as high-surprise event tied to h_4471.

**Day 84 — Mentoring session 2.**
Owner sees the proposed update. Reviews the 4 recent contradictions. Approves a tiered version.
- v1 superseded: `status: superseded, superseded_by: h_4889`
- v2 born as h_4889: `confidence: 0.7, status: active, version: 2`

**Days 85-180.**
v2 is used 47 times. 41 successes, 4 overrides, 2 prediction misses.
- 41 × increment, 4 × 0.85 multiplier, 2 × 0.92 multiplier
- Net climb to ~0.86

**Day 195 — Sleep cycle Job 1.**
Counterfactual evaluation: 5 decisions in last 30 days where charging 50%+ on government buildings would have been accepted easily. Regret signal accumulates.
- Regret trigger fires after 3rd regret signal
- Question added to mentoring queue: "May be undercharging on government work"

**Day 200 — Mentoring session 6.**
Owner reviews. Approves a third tier for government buildings.
- v2 superseded: `status: superseded, superseded_by: h_5042`
- v3 born as h_5042: `confidence: 0.7, status: active, version: 3`

**Days 201-365.**
v3 performs well. Climbs to 0.91. No overrides. Counterfactuals confirm the rule.
- `confidence: 0.91, status: active, version: 3`

By the end of year one, the after-hours pricing rule has been refined twice, with full provenance: which decisions triggered each refinement, which mentoring sessions made each change, what reasoning the owner gave. Future Claude calls retrieving "after-hours pricing" only see h_5042 (v3) but the audit trail back to v1 is queryable any time.

### Module ownership

When we build, the lifecycle logic lives across these modules:

- `storage/heuristics.py` — schema, versioning, status transitions
- `learning/confidence.py` — all the evidence-based increment/decrement math (override penalty, prediction met/miss, stress-test fragility)
- `sleep/counterfactuals.py` — regret signal accumulation (Job 1)
- `sleep/archival.py` — rule archival (Job 2)
- `sleep/replay.py` — surprise replay (Job 3)
- `sleep/stress_test.py` — fragility detection (Job 4)
- `sleep/conflict.py` — conflict detection (Job 5)
- `sleep/working_memory.py` — cache cleanup (Job 6)
- `sleep/autonomy.py` — autonomy re-evaluation (Job 7)
- `sleep/mentoring_scheduler.py` — next-session planning (Job 8)
- `mentoring/triggers.py` — the five triggers and priority scoring
- `mentoring/proposals.py` — drafting proposed updates
- `mentoring/approval_flow.py` — owner UI flow

The Orchestrator's hot path doesn't touch most of this. Confidence increments happen async after decisions close. Almost all the refinement work is batched into Sleep cycle and mentoring. The only synchronous lifecycle code in the hot path is reading status and confidence at retrieval time.

### Tunable parameters

All the magic numbers above are configurable per user in `config.yaml`:

```yaml
confidence_dynamics:
  success_increment: 0.02
  override_multiplier: 0.85
  prediction_miss_multiplier: 0.92
  prediction_met_increment: 0.03

archival:
  min_days_unused: 90

heuristic_birth:
  initial_confidence_mentoring: 0.6
  initial_confidence_pattern: 0.5
  initial_confidence_onboarding: 0.7
  initial_confidence_ingestion: 0.5
  initial_confidence_update: 0.7

triggers:
  drift_days: 60
  override_rate_threshold_30d: 0.20
  regret_count_threshold: 3
  regret_window_days: 60
  conflict_minimum: 1

retrieval_scoring:
  fragile_multiplier: 0.7
  recency_decay_per_day: 0.005
```

Different businesses may want different sensitivity. A high-volume B2C business might tune `success_increment` lower (more evidence needed) and `min_days_unused` shorter (world changes faster, archive sooner). A low-volume B2B business might do the opposite.

---


## Part 24 — Skills

Skills are the unit of work in Solomon. Almost every named operation the brain performs is implemented as a skill that the orchestrator calls by name. The orchestrator's job is largely: figure out which skill to call, load it, run it, validate its output, and store the result in the right place.

This part defines what a skill is, the strict contract every skill must satisfy, the full registry of skills the orchestrator calls, how multi-skill operations are chained, and how the setup flow creates the empty slots where future skills will live.

### Why this pattern

The brain's behavior should be editable without code changes. If "how Solomon conducts a belief interview" is a SKILL.md file, you can improve the interview by editing markdown, no Python deployment, no rebuild. New skill versions roll out on the next worker redeploy.

This is not an agentic system. The orchestrator decides what skill to call. The skill does its job. The orchestrator stores the output. Next skill. This is deterministic by design. Sleep cycle jobs run in a fixed order. Mentoring sessions follow a script. The decisions are made by code; the prompting and reasoning is delegated to skills.

### The line between code and skill

A skill exists where Claude is doing the reasoning. A piece of code exists where Python is just shuffling data.

- Parsing a date, writing to a Postgres table, retrying on failure, scheduling a cron job → code.
- Generating mentoring questions, classifying intent, drafting a daily report, deciding whether a heuristic conflict matters → skill.

When in doubt: if the operation involves Claude reading context and producing a structured judgment or text output, it is a skill.

### Two kinds of skills

**System skills.** Bundled with Solomon, shipped in the GitHub repo, updated with Solomon releases. Read-only at runtime. Examples: foundation interview sessions, audit gate, daily report generator. The full registry is below.

**User skills.** Learned by the brain over time, or written by the user. Stored in the user's Supabase. Editable. Updated by sleep cycle jobs when the brain detects a new pattern worth packaging.

### Skill folder structure

```
skills/<skill-name>/
├── SKILL.md           # the prompt and instructions for Claude
├── metadata.yaml      # name, version, trigger, schemas, output destination
├── input_schema.json  # JSON Schema for input validation
├── output_schema.json # JSON Schema for output validation
├── examples/          # optional few-shot examples
└── python/            # optional helper code (rare)
```

### SKILL.md format

The SKILL.md is the heart of the skill. It is loaded as the Claude system prompt when the orchestrator calls this skill. It contains:

- The role and goal of this skill
- Inputs it expects (described in plain English; the JSON Schema is the strict contract)
- Output format (same)
- Reasoning approach
- Edge cases and what to do
- Few-shot examples if any

This format is intentionally close to Anthropic's published skill format so existing tools work.

### metadata.yaml format

```yaml
name: belief-and-worldview
version: 1.0.0
type: system                      # or "user"
category: onboarding              # see categories below
trigger:
  type: orchestrator              # how this skill gets called
  called_by: onboarding_sequencer # which orchestrator function calls it
input_schema: input_schema.json
output_schema: output_schema.json
output_destination:
  type: supabase_table            # where the orchestrator stores the output
  target: foundation_files
  primary_key: file_path          # foundation_files/belief_system.yaml
model: claude-opus-4-7            # which Claude model to use
max_tokens: 4096
when_to_use: |
  Run during onboarding Session 1. Conducts the belief and worldview
  interview through the Telegram bot (text-based). Output is a populated
  belief_system.yaml structure.
dependencies: []                  # other skills this skill needs to have run first
deprecated: false
```

### The skill contract (strict)

Every skill must satisfy three rules. The orchestrator enforces them at load time. A skill that fails any rule is not loaded and an error is logged.

1. **Declared inputs and outputs.** Every skill has an `input_schema.json` and `output_schema.json`. The orchestrator validates the input before sending it to Claude and validates the output before storing it. If validation fails, the orchestrator retries up to 2 times with the validation errors appended to the prompt; if it still fails, the orchestrator escalates to the owner via Telegram (or, for sleep cycle skills, logs the failure for review in the morning report).

2. **Declared output destination.** Every skill says where its output goes. Five destination types exist:
   - `supabase_table` — write a row to a named table
   - `supabase_file` — write a YAML or JSON file to Supabase Storage at a path
   - `local_yaml` — update a foundation YAML in the local desktop cache (also writes through to Supabase)
   - `redis_key` — write to a working memory key
   - `telegram_message` — send a Telegram message (the message body IS the output)
   - `return_value` — return to the calling skill or workflow without persisting (used for skills inside chains)

3. **Pure function semantics.** A skill takes inputs, produces outputs. It does not reach out to other skills or services itself. If a skill needs the output of another skill, the orchestrator runs the other skill first and passes the result in. This keeps skills testable, composable, and debuggable.

### Skill version pinning for in-flight operations

A 30-day onboarding sprint may start with skill `belief-and-worldview v1.4`. Mid-sprint a new release ships v1.5 with a different output schema. The user is mid-Session 1.

Rule: an in-flight operation pins to the skill version that started it. The pin is recorded when the operation begins (in the `operations` table; see Part 27). The orchestrator loads the pinned version even after a release. The new version takes effect for the next operation that starts.

Pinning applies to:
- Onboarding sessions (one pin per session)
- Mentoring sessions (one pin per session)
- Sleep cycle nightly runs (one pin per night, all 8 jobs share the pin so they're consistent)
- Reports (one pin per report)

The pin is released when the operation completes.

### Multi-skill chains (workflows)

Some operations are naturally multi-step. The mentoring session for week 4: pick questions skill → ask question skill → process answer skill → update foundation skill, in a loop until the session ends.

These are defined as workflow files, separate from skills.

```yaml
# workflows/mentoring_session.yaml
name: mentoring_session
version: 1.0.0
description: A scheduled or triggered mentoring conversation with the owner. Used for both reactive and training sessions.
inputs:
  session_type: string         # reactive or training
  session_subtype: string      # for reactive: weekly, conflict_review, etc. for training: scheduled, on_demand
  surprise_log: array          # populated when session_type is reactive
  gap_analysis: object         # populated when session_type is training
steps:
  - if: $inputs.session_type == "reactive"
    skill: mentoring-pick-reactive-questions
    in:
      session_subtype: $inputs.session_subtype
      surprise_log: $inputs.surprise_log
    out: questions
  - if: $inputs.session_type == "training"
    skill: mentoring-training-gap-analyzer
    in:
      session_subtype: $inputs.session_subtype
    out: questions
  - loop:
      over: $questions
      as: question
      steps:
        - skill: mentoring-ask-question
          in:
            question: $question
          out: answer
        - skill: mentoring-process-answer
          in:
            question: $question
            answer: $answer
          out: extracted
        - skill: mentoring-update-foundation
          in:
            extracted: $extracted
            session_type: $inputs.session_type
          out: write_result
  - skill: mentoring-session-summary
    in:
      session_type: $inputs.session_type
      results: $loop.results
    out: summary
final_output: summary
```

Workflows are themselves first-class. They are versioned, edited like skills, and live in the same skill registry. The orchestrator runs a workflow by stepping through its YAML and calling each skill at each step.

### How skills load and run

When the orchestrator decides to call a skill (by name), it:

1. Looks up the skill in the in-memory registry (rebuilt at worker startup and on user-skill change).
2. If an in-flight operation pin applies, loads the pinned version. Otherwise loads the latest active version.
3. Validates the input against `input_schema.json`. If invalid, raises immediately.
4. Builds the Claude API call: SKILL.md as the system prompt, runtime input as the user message, model and max_tokens from metadata.
5. Sends to Claude. Parses the response.
6. Validates the output against `output_schema.json`. If invalid, retries up to 2 times with errors appended; if still invalid, escalates.
7. Routes the output to the declared destination.
8. Logs the call: skill name, version, input hash, output hash, claude tokens used, duration, success/failure.

### Three layers of work: skill, preset prompt, pure code

Not every operation needs the full skill machinery. Solomon has three layers, and the orchestrator decides which layer to use based on three questions:

1. **Is the prompt long enough that I'd want to edit it without redeploying code?** (more than ~500 words of instructions, examples, edge cases)
2. **Is the output structured enough that schema validation matters?**
3. **Will I want to version it because the prompt will evolve based on what I learn?**

Three "yes" answers means it's a **skill**. The full SKILL.md, schemas, version pinning, registry entry.

Mostly "yes" but the prompt is short and stable means it's a **preset prompt**. A short string constant in the worker codebase. The orchestrator builds the Claude call inline using the constant. No metadata, no version pinning. Examples: salience scoring, event classification, intent classification, non-negotiable checking. The prompt for each is a few sentences. It's stable. Versioning would be overkill because there's barely anything to version. Preset prompts evolve with the codebase via git.

No Claude in the loop at all means it's **pure code**. Webhook receivers, cron schedulers, database transactions, integration adapters, working memory writes, the skill engine itself, the autonomy threshold checks (which are just counts and percentages). Pure Python.

### The promotion rule

If a preset prompt grows past 800 words, or starts needing few-shot examples, or accumulates more than 3 edge cases — it gets promoted to a skill. This is a one-time refactor. The rule prevents preset prompts from quietly becoming large unmaintained pieces of behavior that nobody can edit without a code change.

### Where preset prompts live

A `prompts/` directory in the worker, one file per category:

- `prompts/classification.py` — salience, event type, intent, non-negotiable check
- `prompts/extraction.py` — directive extraction, sensitivity filter, cross-reference
- `prompts/utility.py` — rule archival check, status handler, simple summarization

Each prompt is a Python constant. The orchestrator imports and calls it directly. The Claude call is short and inline.

### What this looks like in totals

Reasoning through every operation Solomon performs:

- About **30 skills** (substantial, editable, versioned). Onboarding sessions, audit gate, System 2 reasoner, mentoring flows, sleep cycle reasoning jobs, report writers, ingestion extractors, conversation responders, learning skills.
- About **12 preset prompts** (short, stable, in code). Classification calls, extraction calls, utility calls, System 1 predictor.
- The rest is **pure Python code**. Capture, infrastructure, routing, storage operations, integrations, the skill engine itself, autonomy math, prediction checking.

The full breakdown of which operation falls in which layer lives in the companion document `solomon-build-inventory.md`. That document is the build backlog for skills, preset prompts, and pure-code modules.

### How the orchestrator handles each layer

```python
# Skill call: heavy machinery
result = skill_engine.run("audit-gate", input_data)

# Preset prompt call: lightweight inline
from prompts.classification import SALIENCE_PROMPT
result = claude.call(system=SALIENCE_PROMPT, user=event_text, response_format="json")

# Pure code: no Claude
db.insert("decisions", decision_row)
```

The orchestrator code is mostly the third pattern. It calls skills when reasoning is the work. It calls preset prompts for short structured Claude calls. Most of the orchestrator file is plain Python doing wiring.

### How this ties to the goal

The goal is to clone the owner's decision-making over 30 days and run their business after. Skills are the editable layer where the cloning happens — every time the owner edits an audit gate verdict or corrects a mentoring answer, that signal eventually feeds into a SKILL.md update. Preset prompts handle the boring high-volume work that doesn't need to learn (classifying an event as "pricing" vs "scheduling"). Pure code does the plumbing that nobody should ever have to think about.

When you build Solomon, you build the pure code first (Phase -1), the preset prompts as you implement each runtime step (Phase 1-2), and the skills last (after the surrounding system works). The skills are where you'll spend the most time iterating, and they're the easiest to iterate on because changes don't need a code release.



Every skill belongs to one category. Categories drive where skills live in the repo and how they are surfaced to the user.

- `onboarding` — used during the 30-day cloning sprint
- `runtime` — used in the per-event flow (audit gate, intent classifier, etc.)
- `mentoring` — used during mentoring sessions
- `sleep` — used by sleep cycle jobs
- `report` — used to generate daily, weekly, on-demand reports
- `learning` — used by sleep cycle jobs that update heuristics or skills themselves
- `industry_module` — pluggable per-industry follow-up curricula
- `playbook` — multi-step user skills the brain learned (lives only in user skills)

### The system skill registry

This is the full list of skills the orchestrator calls. As the spec evolves, this list is the source of truth for what SKILL.md files need to exist. New skills are added here first, then implemented.

**Onboarding (called during the 30-day sprint, Part 4). Every onboarding interview skill writes to TWO destinations: the structured YAML file AND the `onboarding_sessions` table for transcript persistence.**

| Skill | Output destination | Notes |
|---|---|---|
| `industry-business-selector` | `local_yaml: foundation/industry_profile.yaml` plus `supabase_table: onboarding_sessions` | Stage 1 Step 1. Industry, sub-specialty, business model. |
| `belief-and-worldview` | `local_yaml: foundation/belief_system.yaml` plus `supabase_table: onboarding_sessions` | Session 1 |
| `the-why` | `local_yaml: foundation/why.yaml` plus `supabase_table: onboarding_sessions` | Session 2 |
| `principles` | `local_yaml: foundation/principles.yaml` plus `supabase_table: onboarding_sessions` | Session 3 |
| `ideal-outcomes` | `local_yaml: foundation/ideal_outcomes.yaml` plus `supabase_table: onboarding_sessions` | Session 4 |
| `non-negotiables` | `local_yaml: foundation/non_negotiables.yaml` plus `supabase_table: onboarding_sessions` | Session 5 |
| `domain-map` | `local_yaml: foundation/taxonomy.yaml` plus `supabase_table: onboarding_sessions` | Session 6. Scopes, domains, decision types. |
| `seed-heuristics-from-sessions` | `supabase_table: heuristics` (status: pending_approval) | Reads from `onboarding_sessions` (clean per-session transcripts) plus all foundation YAMLs. Proposes heuristics for owner approval one at a time via Telegram. |
| `industry-module-generator` | `supabase_table: heuristics` plus `supabase_table: onboarding_sessions` plus `local_yaml: foundation/industry_module_questions.yaml` | One skill. Reads the user's industry profile and dynamically generates the right follow-up curriculum for their sub-specialty (e.g., flipping vs landlord vs marketing agency vs commercial cleaner). Asks targeted questions through Telegram, captures answers, drafts industry-specific seed heuristics. |

**Ingestion (Part 25):**

| Skill | Output destination | Notes |
|---|---|---|
| `ingestion-classify` | `supabase_table: ingested_documents` | Classify each uploaded document. |
| `ingestion-chunk` | `supabase_table: document_chunks` | Type-specific chunking. |
| `ingestion-extract-decisions` | `supabase_table: historical_decisions` | Pull decisions from chunks. |
| `ingestion-mine-heuristics` | `supabase_table: heuristics` (status: pending_review) | Cross-document patterns. |
| `ingestion-cross-reference` | `supabase_table: document_links` | Link related documents. |
| `ingestion-sensitivity-filter` | `supabase_table: ingested_documents` (sensitivity column) | PII / sensitive content flagging. |

**Runtime (called per-event, Parts 5-19):**

| Skill | Output destination | Notes |
|---|---|---|
| `salience-scorer` | `return_value` | Used by orchestrator before classification. |
| `event-classifier` | `return_value` | Determines scope and decision type. |
| `non-negotiable-checker` | `return_value` | Detects hard-rule violations. |
| `system-1-predictor` | `return_value` | Fast rule-based prediction (Sonnet). |
| `system-2-reasoner` | `return_value` | Full-context reasoning (Opus). |
| `audit-gate` | `return_value` | Approve / downgrade / reject / rethink. |
| `state-band-calculator` | `redis_key: state_band:today` | Whoop-driven autonomy modulation. |
| `intent-classifier` | `return_value` | For conversation mode. |
| `directive-extractor` | `return_value` then `supabase_table: heuristics` (status: pending_review) | Extracts heuristic candidates from conversation. |
| `conversation-question-responder` | `telegram_message` | Answers owner questions in conversation. |
| `conversation-brainstorm-responder` | `telegram_message` | Engages in brainstorm dialog. |
| `conversation-status-handler` | `redis_key: working_memory:*` plus `telegram_message` | Handles status updates. |
| `discuss-button-handler` | `telegram_message` | Opens dialog when owner taps Discuss. |

**Mentoring (Part 21). Two flavors: reactive (responds to events) and training (proactive gap-filling).**

| Skill | Output destination | Notes |
|---|---|---|
| `mentoring-schedule-reactive` | `supabase_table: mentoring_sessions` | Decides when to schedule a reactive session based on accumulated triggers (surprise log, conflicts, override rate). |
| `mentoring-pick-reactive-questions` | `return_value` | Selects questions for a reactive session based on surprise log, conflicts, override patterns. |
| `mentoring-training-gap-analyzer` | `return_value` | New. Reads foundation, heuristics, decision log, surprise log, all past asked questions. Identifies gaps in coverage, edge cases, counterfactuals, philosophical territory. Generates a candidate question list. |
| `mentoring-training-scheduler` | `telegram_message` plus `supabase_table: training_pressure_log` | New. Computes the training pressure score nightly. If pressure crosses a threshold, proposes a training session via Telegram. Respects all caps (max 1 proposed per week, no proposals during onboarding sprint, etc.). |
| `mentoring-ask-question` | `telegram_message` | Asks one question, waits for answer. Used by both reactive and training sessions. |
| `mentoring-process-answer` | `return_value` | Extracts updates from the answer. Used by both. |
| `mentoring-update-foundation` | `local_yaml: foundation/*.yaml` plus `supabase_table: heuristics` plus `supabase_table: training_signals` (when training session) | Writes foundation file changes and heuristic creation. Training-session calls additionally write a `training_signals` row capturing the gap and the fill. |
| `mentoring-session-summary` | `telegram_message` plus `supabase_table: mentoring_sessions` | Wraps the session. |

**Sleep cycle (Part 22). Each is its own skill, run in fixed order:**

| Skill | Output destination | Notes |
|---|---|---|
| `sleep-1-hindsight-check` | `supabase_table: predictions` (resolution column) | Compare predictions to outcomes. |
| `sleep-2-counterfactual-eval` | `supabase_table: counterfactuals` (resolution column) | Evaluate the alternative paths. |
| `sleep-3-surprise-replay` | `supabase_table: surprise_log` plus `supabase_table: mentoring_questions_queue` | Pull high-surprise events; queue mentoring questions. |
| `sleep-4-stress-test-rules` | `supabase_table: heuristics` (status column) | Probe rules for fragility. |
| `sleep-5-conflict-detection` | `supabase_table: heuristic_conflicts` | Find heuristics that contradicted in the same decision. |
| `sleep-6-rule-archival` | `supabase_table: heuristics` (status: archived) | Archive rules unused for 60 days. |
| `sleep-7-autonomy-reevaluation` | `supabase_table: scope_autonomy` | Apply promotion / demotion thresholds. |
| `sleep-8-issue-fix-aggregation` | `supabase_table: report_signals` | Aggregate the day's issues and fixes for report generators. |

**Reports (Part 19):**

| Skill | Output destination | Notes |
|---|---|---|
| `daily-report-generator` | `telegram_message` plus `supabase_table: reports` | 7am morning report. |
| `weekly-report-generator` | `telegram_message` plus `supabase_table: reports` | Sunday/Monday morning. |
| `on-demand-report-generator` | `telegram_message` | When owner asks in conversation. |

**Learning (called by sleep cycle, but distinct category):**

| Skill | Output destination | Notes |
|---|---|---|
| `heuristic-version-bump` | `supabase_table: heuristics` (new version row) | Apply approved heuristic edits. |
| `heuristic-promote-pending` | `supabase_table: heuristics` (status: active) | Move pending heuristics to active after owner approval. |
| `playbook-extractor` | `supabase_table: user_skills` | Detect a multi-step pattern and package it as a user skill. |
| `playbook-improver` | `supabase_table: user_skills` (new version) | Refine an existing user skill based on new evidence. |

**Agent workforce (Part 26):**

| Skill | Output destination | Notes |
|---|---|---|
| `delegate-to-agent-workforce` | `supabase_table: agent_projects` plus Paperclip ticket creation | Called when an event is classified `shape: project`. Builds a Paperclip ticket with full goal context, foundation context, budget cap, and assigned agent. |
| `paperclip-hire-agent` | `supabase_table: agent_projects` plus Paperclip agent creation | Proposes a new agent role to the owner via Telegram. On approval, creates the agent in Paperclip with role description, heartbeat, budget, and approval gates. |
| `paperclip-process-ticket-update` | `return_value` | Called by the poller when a Paperclip ticket has new activity. Decides whether the update is routine (log it), strategic (draft a one-tap to the owner), or a final deliverable (run audit gate, then ship). |
| `agent-callback-responder` | `return_value` (becomes a Paperclip ticket comment) | When an agent asks Solomon for guidance via `@solomon` mention on a ticket, this skill loads the foundation, runs System 2 reasoning on the question, and returns the answer as a comment. |

### The bootstrap process at setup

When a new user runs the wizard, the system automatically creates every place a skill output will land. This happens during Screen 3 (Connect Supabase) and Screen 5 (Provision worker) of the setup flow.

The bootstrap migration creates:

1. **Supabase tables.** Every table named in the registry above (foundation_files, heuristics, onboarding_sessions, mentoring_sessions, training_signals, training_pressure_log, surprise_log, predictions, counterfactuals, heuristic_conflicts, scope_autonomy, report_signals, reports, ingested_documents, document_chunks, historical_decisions, document_links, user_skills, operations, skill_calls, agent_projects, agent_activity_log, etc.). Schemas defined in Part 27.
2. **Supabase Storage buckets.** `foundation-files/` for YAML mirrors, `ingestion/` for raw uploaded documents.
3. **Redis namespaces.** `working_memory:*`, `state_band:*`, `pending_approvals:*`, `pinned_skills:*`.
4. **Local desktop cache directories.** `~/Library/Application Support/Solomon/foundation/`, `~/Library/Application Support/Solomon/skills_cache/`.
5. **Skill registry seed.** The worker on first startup reads every system skill from its bundled `skills/` directory, validates its metadata.yaml and schemas, and inserts a row into the `skill_registry` table. Workflows are loaded the same way from `workflows/`.
6. **Paperclip integration (deferred).** Paperclip is not provisioned at first wizard run. It's added later when at least one scope has reached `act_alone` status (typically months 2-4). At that point, the wizard re-opens with a "Connect agent workforce" screen that deploys Paperclip on the user's Render or Railway and registers the connection.

After bootstrap, the system is ready to call any skill in the registry. Empty SKILL.md files (placeholders) are fine; the orchestrator will report "skill not yet implemented" if it tries to call one.

### What happens when you (later) write a SKILL.md

You add or edit a SKILL.md in the Solomon repo, ship a release, the worker redeploys, the registry rebuilds, the new skill is callable. No orchestrator code changes needed. No database migration unless you also change the skill's output destination (which is a metadata.yaml change, validated at load).

### The skill index in Telegram

The owner can ask Solomon "show me my skills" or `/skills` and get a list:

> Active skills (24 system, 7 user)
> Recently updated: daily-report-generator (v1.4), audit-gate (v2.1)
> Suggested for review: kickoff-workflow-bridgewater-style (3 owner edits in 2 weeks)
> Disabled: vendor-late-pay-screening (you turned it off May 1)

The owner can `/disable <skill>` and `/enable <skill>` from Telegram. A disabled skill is skipped by the orchestrator, with a logged note. This gives the owner an emergency brake without waiting for a code fix.

### Module ownership

- `skills/system/` — the bundled system skills, shipped in the Solomon repo. One folder per skill.
- `workflows/` — the workflow YAML files. Same shipping path as skills.
- `skill_engine/loader.py` — finds, validates, and indexes skills at worker startup
- `skill_engine/registry.py` — in-memory index keyed by name, with version metadata
- `skill_engine/runner.py` — the function the orchestrator calls; handles validation, retries, version pinning, output routing, logging
- `skill_engine/workflow_runner.py` — steps through workflow YAML, calls runner for each step
- `skill_engine/version_pinner.py` — manages in-flight operation pins
- `skill_engine/output_router.py` — handles each of the 6 output destination types
- `skill_engine/telegram_skill_index.py` — the `/skills` command and enable/disable handlers
- User skills live in Supabase in a `user_skills` table, with the SKILL.md content as text and metadata as JSON columns. Schema defined in Part 27.

---


## Part 25 — Ingestion (the document pipeline)

This part covers how the brain absorbs unstructured documents — at onboarding (a backlog of years of material) and during operation (ad-hoc additions). This is separate from Capture, which handles real-time events.

### What gets ingested

Anything the owner has that contains decisions, reasoning, context, or knowledge. Examples:

- Old email threads (months or years of history exported from Gmail)
- Past proposals and quotes (Word docs, PDFs)
- Meeting transcripts (from Zoom, Otter, Granola archives)
- Contracts and SOPs (PDFs, Word, Notion exports)
- Customer feedback (CSV exports from review sites, support ticket histories)
- Internal documentation (employee handbook, training materials, process docs)
- Text message exchanges (export from iMessage or WhatsApp)
- Notebooks (Apple Notes, Notion, Google Docs)
- Call recordings (audio files)
- Spreadsheets (pricing histories, vendor lists, schedules)
- Any other artifact that contains business knowledge

### Why ingestion is separate from Capture

Capture is built for real-time, single events. Each event is small, fresh, and timestamped to *now*. The brain decides what to do about it within seconds.

Ingestion is bulk, historical, and slow. A single upload might be 10,000 emails covering 5 years. Each email has its own historical context. The decisions in them have already been made and their outcomes are already known. The processing is fundamentally different:

- Decisions are *extracted retrospectively*, not made
- Outcomes are *known and matched* to their decisions, not predicted
- Context comes from *the document set itself*, not from working memory
- Time is reconstructed, not tracked live
- The owner reviews extracted findings before they go to memory

### Two modes of ingestion

**Bulk mode (onboarding).** A large pile uploaded at the start. Processed over days or weeks. Owner reviews findings in batches. Goal: turn historical artifacts into seed memory so the brain doesn't start at zero.

**Ad-hoc mode (ongoing).** A few documents added as they appear. "Here's the transcript from yesterday's strategy meeting." "Here's the new policy we just wrote." Smaller batches, faster turnaround. Goal: continuously enrich memory as new material is created.

Both go through the same pipeline. The only difference is volume and review cadence.

### The ingestion pipeline

For each document or batch:

**Stage 1 — Upload and queue.**
The owner uploads through the desktop app's upload UI (drag a folder; the app forwards files to the worker) or sends documents through Telegram. Files land in Supabase Storage. A row is created in `ingestion_jobs` with status `queued`.

**Stage 2 — Type classification.**
Claude reads the first chunk of each document and classifies:
- Document type (email thread, proposal, transcript, contract, etc.)
- Time period (when was this written or about?)
- Participants (who is involved?)
- Domain (what part of the business?)
- Salience estimate (how important does this look?)

Output: `ingestion_documents` row with metadata. Status: `classified`.

**Stage 3 — Chunking and embedding.**
The document is split into chunks based on its type. Email threads split by message. Transcripts split by speaker turn or topic shift. Contracts split by section. Each chunk gets an embedding. Stored in pgvector with `source: ingestion`, linked back to the original document.

**Stage 4 — Decision extraction.**
For each chunk that looks like it contains a decision, Claude extracts:
- What was the situation?
- What options were considered?
- What was decided?
- What was the reasoning?
- What was the outcome (if visible in the document)?
- Who made the decision?
- When?

Each extracted decision becomes a row in the `decisions` table with `source: ingestion`, marked as `historical: true` so it's distinguishable from live decisions.

Historical decisions don't carry predictions or counterfactuals (the future is already known). They get embedded and become part of the retrieval pool.

**Stage 5 — Heuristic mining.**
After all documents in a batch are processed, Claude does a pass across all extracted decisions looking for repeated patterns. Example: "In 23 of the 31 extracted pricing decisions, after-hours work was charged 20-25% above base. This looks like an implicit rule."

These pattern-matched proposals go into `pending_heuristics` for owner review. They are *not* automatically promoted — owner approval is required.

**Stage 6 — Cross-referencing.**
Documents reference each other. A proposal might reference an earlier email. A contract might supersede a prior contract. Claude detects these references and adds links so retrieval can follow them.

**Stage 7 — Owner review.**
The owner sees a digest:
> "Processed 1,847 emails covering Mar 2020 - Sep 2024. Extracted 312 decisions. Detected 28 candidate heuristics. Found 14 multi-step processes that look like skills. Review?"

The owner reviews in batches:
- For each candidate heuristic: approve, edit, reject, defer
- For each candidate skill: same
- For each high-salience extracted decision: confirm the extraction is accurate

Approved items are committed. Rejected items are still kept in storage as historical decisions, just not promoted to heuristics or skills.

### What about decisions the owner didn't make?

Some documents contain decisions made by employees, vendors, or customers, not the owner. These are still useful — they're context — but they shouldn't be treated as the owner's expressed wisdom.

During Stage 4, Claude tags every extracted decision with `decision_maker`. If `decision_maker != owner`, the decision is logged but does not feed the heuristic mining pass. It's purely context.

### Privacy and sensitivity filtering

Some documents contain personal, legal, or otherwise sensitive material that shouldn't be embedded or processed. Before Stage 3, every document passes a sensitivity filter:

- PII (social security numbers, passport numbers, etc.) — auto-redacted before embedding
- Legal correspondence with attorneys — flagged, owner can opt to skip
- Personal/family material accidentally included — flagged for owner review

The owner can mark any document as `sensitive: true` at upload time, which limits processing depth and excludes the document from cross-user pattern analysis (if we ever do that).

### Ingestion scheduling

Bulk ingestion runs in the background. The pipeline is rate-limited so it doesn't blow the token budget:

- Default: process up to 100 documents per day during onboarding
- Owner can increase if they want faster ingestion (and pay for it)
- Sleep cycle window (2am-5am) is preferred for heavy processing

For ad-hoc ingestion, smaller batches (under 10 documents) are processed within an hour. Larger ad-hoc batches go to overnight processing.

### Token budgeting for ingestion

Ingestion is the highest-token-cost activity in the system. To control cost:

- Documents below salience 0.3 (auto-estimated) get only Stage 1-3 (classification, chunking, embedding) — no decision extraction
- Documents above salience 0.3 get Stages 1-6
- High-salience documents (>0.7) get extra attention: deeper extraction, multiple Claude passes, more careful cross-referencing

Per-user budget cap: configurable, default $50/month for ingestion. Hits the cap → ingestion pauses, owner is notified.

### What happens to ingested decisions in retrieval

Historical decisions are first-class citizens in retrieval. They show up in:
- Semantic lane (vector similarity)
- Entity lane (decisions involving the same client, vendor, employee)
- Pressure lane (decisions made under similar conditions)

But they get a small recency penalty because they're old:
```
recency_factor = exp(-recency_decay * (days_since_decision_was_made))
```

So ingested decisions help most when the topic is genuinely about something old (a returning client, a recurring situation), and matter less for fresh topics.

### Re-ingestion

If the owner discovers a better source for something already ingested (e.g., they had only the email thread before, now they have the meeting transcript that explains the email), they can re-ingest. The new document creates a new set of extractions. The old extractions stay but are marked `superseded_by: <new_extraction_ids>`.

### Module ownership

When we build:
- `ingestion/upload_handler.py` — file uploads, queueing
- `ingestion/classifier.py` — document type and metadata classification
- `ingestion/chunker.py` — type-specific chunking
- `ingestion/embedder.py` — embedding generation and storage
- `ingestion/extractor.py` — decision extraction from chunks
- `ingestion/heuristic_miner.py` — cross-document pattern detection
- `ingestion/cross_referencer.py` — document linking
- `ingestion/sensitivity_filter.py` — PII redaction and sensitive content flagging
- `ingestion/review_queue.py` — owner review workflow
- `ingestion/budget_tracker.py` — token cost tracking and rate limiting

The ingestion pipeline runs inside the hosted worker (Part 2). Uploads come in two ways: through a small upload UI in the desktop app (the user drags a folder, the desktop app forwards to the worker), or through Telegram for one-off documents.

---

## Part 26 — The agent workforce (Paperclip integration)

### Why this exists

Solomon's runtime pipeline (Parts 5-19) handles single events. An email arrives, Solomon reasons about it, an action ships. That's the right model for short-lived decisions: send a reply, update a record, post a Slack message.

It's the wrong model for work that takes hours or days. Examples:

- "Find a new plumber for the Maple project. Get three quotes. Schedule the site visits."
- "Run the weekly social media campaign across LinkedIn and Instagram."
- "Negotiate the lease renewal with the landlord at Henderson Plaza."

These are not single events. They are jobs that span many steps, need their own working memory, and want to run over time without the user (or Solomon) babysitting each step. To run a business in Phase 3, Solomon needs workers who can take on these jobs and report back.

That layer is the agent workforce. Solomon integrates with Paperclip to provide it.

### What Paperclip is

Paperclip is an open-source platform that orchestrates a team of AI agents the way a company orchestrates a team of employees. Each agent has a role, a heartbeat (how often it wakes to check its work queue), a budget (so a runaway agent cannot drain the user's API account), and an approval workflow (sensitive decisions wait for human confirmation).

Paperclip does not build agents. Each agent is a separate program (a Claude Code session, an OpenClaw bot, a Python script, an HTTP webhook). Paperclip provides the org chart, the ticketing system, the budgets, and the audit trail. It is the company; the agents are the employees.

For Solomon's purposes, Paperclip is the layer where multi-day jobs live. Solomon hands off a job to a Paperclip agent, the agent works on it across many heartbeats, and the result eventually comes back to Solomon for review and (when needed) owner approval.

### Who's the boss

Solomon is the Board, in Paperclip's terms. Solomon owns the agents, sets the budgets, and approves the strategic moves they propose. The owner never sees Paperclip directly. The owner sees Solomon's Telegram bot. Solomon is the single interface.

This preserves the core promise of the system: one interface (Telegram), one decision-maker (Solomon). Solomon happens to use a workforce under the hood the same way a human CEO uses a project management tool. The owner doesn't need to know.

### Where the seam is

The Conductor decides whether a given event needs a one-shot action (existing pipeline, Part 17) or a multi-step project (Paperclip). The decision is made early, right after classification (Part 8). A new internal field on every classified event marks it `shape: short_lived` or `shape: project`.

- `shape: short_lived` — proceeds through the existing pipeline. Reasoning, audit, action, done.
- `shape: project` — gets handed to the Paperclip integration skill. The skill creates a ticket, assigns the right agent, sets a budget, and returns a project_id. The Conductor logs the project and moves on. The agent works asynchronously.

Most events are short-lived. Project-shape events are the exception, not the rule. The point of the agent workforce is to absorb the rare jobs that don't fit the per-event flow, not to replace the per-event flow.

### What an agent looks like in Solomon

An agent in Solomon's Paperclip company is a named role with a job description, a heartbeat schedule, a budget, and a set of skills it knows how to use. Agents Solomon manages by default:

- **Marketing agent** — posts to social, drafts email campaigns, monitors engagement
- **Vendor coordinator** — finds vendors, gets quotes, schedules visits, follows up
- **Bookkeeping agent** — categorizes transactions, prepares invoices, flags anomalies
- **Customer support agent** — handles routine inbound questions, escalates the rest
- **Project manager agent** — tracks active projects, follows up on stalled tasks

The exact agent set depends on the user's business. Each is created during onboarding (or later, on demand) by a `paperclip-hire-agent` skill that uses the user's industry profile, taxonomy, and recent decision history to propose roles. The owner approves each hire via Telegram before the agent is active.

### How a project flows

1. **Event arrives** at Solomon. Classified as `shape: project` based on its scope and the work involved.
2. **Conductor calls** the `delegate-to-agent-workforce` skill. The skill builds a ticket: title, full goal context (so the agent knows why), the relevant foundation context, the budget cap.
3. **Paperclip assigns** the ticket to the right agent based on the ticket's category and the org chart.
4. **Agent works** on the ticket across many heartbeats. Each heartbeat: check task queue, do the next step, update the ticket, sleep.
5. **Agent posts back** progress, intermediate results, or a completed deliverable. If the agent needs strategic input ("which vendor of these three?"), it asks via the ticket.
6. **Solomon polls** Paperclip on a schedule (configurable, default every 5 minutes). New ticket activity is pulled into Solomon as a `RawEvent` with `source = paperclip_ticket_update`.
7. **Solomon decides** what to do with the update. Routine progress logs go to working memory and the daily report. Strategic questions get drafted as one-tap suggestions to the owner. Final deliverables ready to ship get the audit gate treatment, then go through Solomon's normal action layer.
8. **Owner sees** the relevant moments in Telegram, makes one-tap decisions when needed, and reads about the rest in the daily report.

### Trust and safety, applied to agents

Three layers of safety:

1. **Per-agent budgets.** Every agent has a monthly budget. At 80% utilization, soft warning. At 100%, the agent auto-pauses and stops accepting new tickets. Owner can override and resume.
2. **Approval gates.** Every agent has a list of actions that require explicit approval before they ship. Sending an email to a real customer. Spending more than $X on a vendor. Hiring another agent. Approval flows back through Solomon to Telegram, never directly from Paperclip to the owner.
3. **Audit log.** Every action every agent takes is logged in Paperclip's append-only activity log. Solomon mirrors the agent activity into its own decision log so reports and mentoring sessions can reason over what the agents did.

The owner state gate (Part 14) applies to agents too. On red-band days, all agent approval gates are escalated regardless of scope: nothing ships without the owner explicitly approving.

### How agents learn

Agents do not have their own brain. They consult Solomon. When an agent is making a non-trivial judgment ("should I send this draft email to the lead?"), the agent calls back to Solomon's brain through the System 2 reasoner. Solomon reasons using the user's foundation, heuristics, and active memory, and returns the answer. The agent acts on it.

This is what keeps the agent workforce aligned with the owner. Without this, you'd have agents acting on their own judgment, which would gradually drift from the owner's. With it, every meaningful decision the agents make is still a Solomon decision; the agents just do the legwork.

The corollary: agents do not get smarter by themselves. They get smarter when Solomon's brain gets smarter. All learning still happens in the brain.

### Where data lives

- **Paperclip's own tables.** Org chart, agents, tickets, ticket activity, budgets, approvals, audit log. Paperclip handles its own database (a separate Postgres database, by default a managed Supabase project just like Solomon's own data, or the same Supabase project with a `paperclip_` schema prefix).
- **Solomon's tables.** A new `agent_projects` table tracks which Paperclip projects exist, what they're for, and their current state from Solomon's perspective. A new `agent_activity_log` mirrors agent actions for Solomon's reasoning and reporting.

Both are bootstrapped during setup (Part 3). The wizard adds a new screen for connecting Paperclip: install Paperclip on the user's Render or Railway account using a one-click deploy template, then enter the connection URL and API key.

### What this changes in the existing parts

The integration is additive. The existing pipeline doesn't change for short-lived events. Three small additions elsewhere:

- **Part 8 (Classification):** the classifier now also assigns `shape: short_lived` or `shape: project` to every event. Most events are short-lived; the rule is conservative (only mark `project` when the work clearly spans hours or more).
- **Part 17 (Action layer):** unchanged. Short-lived events still flow through here.
- **Part 19 (Reports):** the daily and weekly reports now include an "agent workforce" section summarizing what the agents shipped, what's pending, and what hit a wall. This is generated by the existing report skills with one additional Reads-from source: the `agent_activity_log`.

### When to introduce this

Not in the 30-day onboarding sprint. Solomon spends the first 30 days learning the owner. Adding an agent workforce on top of that would dilute the focus and confuse the owner.

Paperclip integration starts proposing itself once one or more scopes have reached `act_alone`. At that point, the brain has been trusted to act on its own in some scope, and it makes sense to ask: "Do you want me to start delegating multi-day work in this scope to a worker agent?" The owner says yes, the wizard's Paperclip screen runs, and the agent workforce is born.

For most users this is somewhere in months 2-4. The Phase 3 reporting phase (Part 0) is when Paperclip is fully active.

### Module ownership

- `paperclip/client.py` — wraps the Paperclip API
- `paperclip/poll.py` — polls Paperclip every 5 minutes for ticket activity, creates `RawEvent` rows
- `paperclip/setup.py` — provisioning helper called by the wizard
- `agent_workforce/delegate.py` — invoked by the `delegate-to-agent-workforce` skill (see Part 24, system skill registry)
- `agent_workforce/agent_callback.py` — handles inbound calls from agents asking Solomon for guidance (these come in as Paperclip ticket comments tagged `@solomon`)
- `agent_workforce/budget_monitor.py` — watches per-agent budgets, escalates approaching caps to Telegram

---


## Part 27 — Storage schema (the database)

### Postgres tables (hosted in Supabase)

**decisions** — every decision, full metadata. See Part 16 for columns.

**heuristics** — extracted rules.
```
heuristic_id
scope, domain
condition (what triggers this)
action (what to do)
reasoning (why)
confidence
last_used_at, last_retrieved_at, last_updated_at
source (mentoring, pattern_engine, ingestion, onboarding)
provenance (which decisions support it, which mentoring session it came from)
status (active, fragile, archived)
version
superseded_by (if a newer version exists)
```

**skills** — multi-step playbooks.
```
skill_id
scope, domain
name
trigger_condition
steps (JSON array of step objects with title, instruction, expected_outcome)
success_criteria
source_decisions (which decisions inspired this skill)
confidence
version
```

**predictions** — checkpoint forecasts.
```
prediction_id, decision_id, prediction_text, expected_by, status, actual_outcome, checked_at
```

**counterfactuals** — alternative-path forecasts.
```
counterfactual_id, decision_id, alternative_choice, predicted_outcome, evaluated_at, would_have_been_better (boolean)
```

**mentoring_sessions** — Q&A history.
```
session_id
session_type (reactive, training, calibration, ad_hoc)
session_subtype (e.g., for reactive: weekly, conflict_review; for training: scheduled, on_demand)
status (in_progress, complete, abandoned)
scheduled_at, started_at, completed_at
paused_at, resumed_at (nullable; sessions can be paused)
transcript_text (full conversation, appended turn-by-turn)
questions (JSON array of question objects asked)
answers (JSON array of user answers)
heuristics_created (JSON array of heuristic IDs)
heuristics_updated (JSON array of heuristic IDs)
foundation_updates (JSON array of foundation file paths edited)
summary_text (set when complete)
```

**onboarding_sessions** — the 6 foundation interview sessions plus industry selector and industry module. Same shape as mentoring_sessions but for onboarding.
```
session_id
session_type (industry_selector, belief_and_worldview, the_why, principles, ideal_outcomes, non_negotiables, domain_map, industry_module)
status (in_progress, complete, paused, abandoned)
started_at, completed_at
paused_at, resumed_at (nullable)
transcript_text (full conversation, appended turn-by-turn)
output_yaml_path (e.g., foundation/belief_system.yaml)
output_yaml_committed_at (nullable; null until the YAML is finalized)
heuristics_seeded (JSON array of heuristic IDs created from this session, populated by seed-heuristics-from-sessions)
```

This table is what `seed-heuristics-from-sessions` reads from. It's also what mentoring sessions can reference when the user wants to "redo" or "extend" a foundation conversation later.

**training_signals** — every gap-and-fill produced by proactive training mentoring (Part 21).
```
signal_id
session_id (FK to mentoring_sessions where session_type='training')
question_text
question_embedding (for semantic dedup against future questions)
gap_type (coverage, confidence, drift, philosophical, hypothetical, edge_case)
scope, domain
answer_text
created_heuristic_ids (JSON array; what heuristics this answer produced)
updated_foundation_paths (JSON array; which YAMLs were edited)
created_user_skill_ids (JSON array; user skills produced from multi-step answers)
asked_at, answered_at
```

This table is the dedicated "training storage." Future training sessions consult it to avoid repeats. Reports can query it to show the user what proactive training has produced over time. The brain can audit its own training history.

**training_pressure_log** — nightly snapshot of the training pressure score, used by the proactive scheduler.
```
log_id
computed_at
override_rate_7d
edit_rate_7d
escalations_per_day_7d
surprise_rate_7d
days_since_last_training
pressure_score (HIGH, MODERATE, LOW, VERY_LOW)
proposed_session_window (e.g., "this_week", "2-3_weeks", "4-6_weeks", "on_demand")
```

**raw_events** — every captured event in original form.
```
event_id, source, received_at, participants, raw_content, channel_metadata, salience_score, processed_at
```

**audit_log** — every audit gate verdict.
```
audit_id, decision_id, verdict, reasoning, model_used, audited_at
```

**pending_approvals** — actions waiting on the owner.
```
approval_id, decision_id, proposed_action, expires_at, status (pending, approved, edited, rejected, expired)
```

**autonomy_state** — current autonomy level per scope.
```
scope, level, since, last_promoted_at, last_demoted_at, override_rate_7d, override_rate_30d
```

### Skill engine tables (Part 24)

**skill_registry** — every system and user skill the orchestrator can call.
```
skill_id (e.g., "audit-gate")
type (system, user)
category (onboarding, runtime, mentoring, sleep, report, learning, industry_module, playbook)
current_version
is_enabled (boolean; owner can disable via Telegram)
disabled_reason (text; null when enabled)
input_schema (JSON Schema)
output_schema (JSON Schema)
output_destination (JSON: type and target)
trigger (JSON: how this skill gets called)
model, max_tokens
deprecated (boolean)
last_called_at, last_succeeded_at, last_failed_at
created_at, updated_at
```

**skill_versions** — historical SKILL.md content for every version, for audit and version pinning.
```
version_id
skill_id (FK to skill_registry)
version (semver string)
skill_md_text (the prompt as shipped)
metadata_yaml (the full metadata at this version)
shipped_at
released_with (Solomon release tag, null for user skills)
```

**skill_calls** — every skill invocation logged.
```
call_id
skill_id, version_used
input_hash (SHA of validated input)
output_hash
input_size_tokens, output_size_tokens
latency_ms
status (success, validation_failed, claude_error, schema_retry_recovered)
error_text (null on success)
operation_id (FK to operations, null for one-off calls)
called_at
```

**operations** — multi-step operations that pin skill versions while in flight.
```
operation_id
type (onboarding_session, mentoring_session, sleep_cycle, report, ingestion_job, workflow_run)
state (running, completed, failed, abandoned)
started_at, completed_at
pinned_skill_versions (JSON: {skill_id: version_id, ...} for every skill the op might call)
inputs (JSON)
final_output (JSON, null if not complete)
error (null on success)
```

**workflow_runs** — instances of multi-skill workflows (Part 24 chains).
```
workflow_run_id
workflow_id, workflow_version
operation_id (FK to operations)
current_step
step_history (JSON array)
state (running, completed, failed)
```

**user_skills** — user-specific skills stored in this user's Supabase only.
```
user_skill_id
skill_name
category (typically "playbook")
current_version
skill_md_text
metadata_json
input_schema, output_schema
created_from (decision_id or mentoring_session_id that produced this)
created_at, updated_at
```

### Sleep cycle and learning tables (Parts 22, 23)

**surprise_log** — high-divergence events queued for sleep replay and mentoring.
```
surprise_id
decision_id (FK)
divergence_score
created_at
processed_in_sleep_at (null until sleep cycle handles it)
queued_for_mentoring (boolean)
```

**heuristic_conflicts** — pairs of heuristics that contradicted in the same decision.
```
conflict_id
heuristic_a_id, heuristic_b_id
decision_id
detected_at
resolved_at (null until owner decides which wins)
resolution (winner, both_modified, both_archived)
```

**scope_autonomy** — same as autonomy_state above; named here for the sleep skill that writes it. (Single table; the spec uses both names interchangeably.)

**mentoring_questions_queue** — questions waiting to be asked in the next mentoring session.
```
queue_id
question_text
source (surprise_replay, heuristic_conflict, owner_directive_repeated, etc.)
source_ref (decision_id, conflict_id, etc.)
priority
queued_at
asked_in_session (null until asked)
```

### Report tables (Part 19)

**report_signals** — issues and fixes detected during the day, fed to report generators.
```
signal_id
type (issue, fix)
subtype (audit_reject, prediction_miss, fragility, conflict, regret, demotion, override_threshold, version_bump, foundation_commit, promotion, unarchive, new_heuristic, pending_acceptance)
ref_table, ref_id
detected_at
included_in_report_id (null until included)
```

**reports** — every daily, weekly, and on-demand report sent.
```
report_id
type (daily, weekly, on_demand)
generated_at
delivered_at (Telegram timestamp)
content_text (the message body sent)
covers_period_start, covers_period_end
signals_included (JSON array of signal_ids)
```

### Ingestion tables (Part 25)

**ingestion_jobs** — every upload batch.
```
job_id, source (desktop_upload, telegram), uploaded_at, status (queued, classifying, chunking, extracting, mining, ready_for_review, complete), progress, total_files
```

**ingested_documents** — one row per document.
```
document_id, job_id, original_filename, document_type, sensitivity_level, classified_at, processed_at
```

**document_chunks** — chunks of documents.
```
chunk_id, document_id, content, chunk_metadata (JSON), embedding_id (FK)
```

**historical_decisions** — decisions extracted from ingested documents.
```
historical_decision_id, document_id, decision_text, outcome_text, decided_at, scope, domain, status (proposed, approved_by_owner, rejected)
```

**document_links** — cross-references between documents.
```
link_id, source_document_id, target_document_id, relationship (replied_to, supersedes, references), confidence
```

### Agent workforce tables (Part 26)

**agent_projects** — every project Solomon has delegated to a Paperclip agent.
```
project_id (Solomon's internal ID, separate from Paperclip's ticket_id)
paperclip_ticket_id
paperclip_agent_id
title
goal_text
foundation_context_snapshot (JSON; the foundation files at delegation time)
budget_cap_usd
created_at
created_from_event_id (FK to raw_events)
status (delegated, in_progress, awaiting_approval, completed, failed, cancelled)
last_activity_at
final_deliverable_text (null until complete)
final_deliverable_decision_id (FK to decisions if a final ship was approved through Solomon)
```

**agent_activity_log** — mirror of every action every agent takes, pulled from Paperclip via the poller.
```
activity_id
project_id (FK to agent_projects)
paperclip_ticket_id
paperclip_agent_id
activity_type (heartbeat_check, comment_posted, status_changed, deliverable_attached, callback_requested, approval_required, budget_warning, budget_exhausted)
content (JSON; the full activity payload from Paperclip)
processed_by_solomon_at (null until paperclip-process-ticket-update has run on this row)
solomon_response (JSON; what Solomon did with this update — logged_only, drafted_to_owner, ran_audit_gate, etc.)
recorded_at
```

This table is what the daily and weekly report skills read to produce the "agent workforce" sections of reports. It's also what mentoring sessions can reference when the owner asks "how did the marketing agent do this week?"

### Vector storage (pgvector inside Supabase)

A single `embeddings` table:
```
embedding_id, source_table (decisions, heuristics, mentoring_sessions, document_chunks, user_skills), source_id, vector (1536-dim), created_at
```

### Working memory (Redis or Postgres with TTL)

Key-value: `key = scope:participant:thread_id`, `value = JSON of recent decisions and active context`, `ttl = 7 days`.

### Foundation files (Supabase + local YAML cache)

```
foundation/
  belief_system.yaml
  why.yaml
  principles.yaml
  non_negotiables.yaml
  ideal_outcomes.yaml
  nice_to_haves.yaml
taxonomy/
  scopes.yaml
  domains.yaml
  decision_types.yaml
```

Foundation files live in Supabase as the source of truth. The desktop app keeps a local YAML cache for fast boot and offline reading. Every change is versioned in Supabase with timestamp, source, and the user_id of the action that triggered it. Provenance is automatic.

---

## Part 28 — Per-user isolation

In Solomon's BYO-cloud architecture, isolation is structural, not a layer of code. Every user has their own dedicated infrastructure end-to-end:

- Their own Anthropic account (Claude API key)
- Their own Supabase project (long-term memory, foundation files, decision log)
- Their own Redis Cloud database (working memory)
- Their own Render or Railway worker (always-on runtime)
- Their own Telegram bot (created via BotFather under their Telegram account)
- Their own credentials stored in the system keychain on their desktop machine

The Solomon project ships software (desktop app, worker code, system skills). It does not host any user data. There is no shared database, no shared queue, no shared memory.

### What this means for the codebase

The orchestrator and all worker code are written assuming a single user. There is no `user_id` column on any table because every Supabase project belongs to one user. There is no tenant routing because every worker runs for one user. This is a major simplification.

### What still needs care

The desktop app and worker do interact with multiple cloud accounts on behalf of the user:

- The wizard reads and writes to the user's Supabase, Redis, Render, and Telegram. It must never accidentally write to the wrong account if a user has multiple identities or runs the wizard twice.
- The export and import feature (Part 2) packages credentials. The format must be encrypted at rest.
- Multi-machine pairing (Part 2) requires a secure handoff between two desktop installations of the same user.

These are addressed in Parts 2 and 3.

### What this means for the user

- Their data never touches Solomon project infrastructure.
- If Solomon (the project) shuts down, their brain keeps running on their own infra.
- If they want to leave, they keep everything: the Supabase project, the decision history, the bot.
- If they want to share with the team, they create additional credentials in their own infra and grant access.

---

## Part 29 — Configuration

### Per-user config file

Each user's worker has a `config.yaml` stored in Supabase and mirrored in the local desktop cache:

```yaml
user_id: marcus_cleaning
business_name: Marcus Commercial Cleaning
timezone: America/Edmonton

owner_interface:
  telegram_chat_id: 123456789
  morning_digest_at: "07:00"
  evening_recap_at: "21:00"
  one_tap_ttl_hours_waking: 4
  one_tap_ttl_hours_overnight: 12

whoop:
  enabled: true
  poll_interval_minutes: 30
  default_band_when_missing: yellow

salience_weights:
  stakes: 0.40
  novelty: 0.30
  emotion: 0.15
  owner_involvement: 0.15

retrieval_weights:
  semantic: 0.30
  recency: 0.20
  entity: 0.25
  pressure: 0.15
  foundation: 0.10

decay_rate: 0.02  # per day
mentoring_cadence: auto

sleep_cycle_window:
  start: 02:00
  end: 05:00

# Sprint mode applies during the first 30 days. After day 30, production
# thresholds (in Part 15) take over automatically.
sprint_mode:
  active_until: 2026-05-31
  decision_count_for_promotion: 20
  override_rate_max_for_promotion: 0.10
  confidence_min_for_promotion: 0.70

autonomy_levels:
  pricing: act_with_approval
  hiring: watch
  scheduling: act_alone
  vendor: suggest
  complaints: suggest
```

### Global config (per worker deployment)

API keys and tokens (Claude, Supabase, Gmail, Twilio, Telegram bot, Whoop OAuth) are passed to the worker as environment variables at deploy time. Each user runs their own worker with their own credentials. There is no central project secrets store.

---

## Part 30 — Failure modes and what to do

### What if Claude is down?

The Orchestrator queues the event and retries with exponential backoff. After 3 failures, escalates to the owner via Telegram with a "system slow" notice.

### What if the audit gate disagrees with itself?

If running the same audit twice gives different results, treat that as low confidence. Always downgrade to suggest mode in this case.

### What if a non-negotiable is unclear?

Better safe than sorry. Treat unclear as a violation. Escalate via Telegram.

### What if the owner is on vacation?

Two paths:
- **Manual.** Owner sends `/vacation` to the Telegram bot. Autonomy drops one level across the board until they return. Mentoring sessions auto-pause.
- **Automatic.** If Whoop indicates the owner is in a different timezone for >48 hours and recovery is unusually high (vacation pattern), the brain proposes: "Looks like vacation. Drop one level until you return? 1 yes 2 no." This is a proposal, never automatic.

### What if Whoop is unreachable?

The owner state gate defaults to `yellow`. Effective autonomy ceiling becomes `act_with_approval` until Whoop is back. The brain doesn't know how the owner is doing, so it errs toward asking.

### What if the owner takes Whoop off?

Same as above — yellow band by default. The owner can override with `/force_normal` to operate at full autonomy without biometric data, but this disables a safety valve and is logged.

### What if Telegram is down?

Pending one-tap suggestions queue locally. Once Telegram recovers, the bot sends them with the original timestamps so the owner sees what was held. Outbound business actions (emails, calendar updates) are not affected — Telegram only carries the owner-facing layer.

### What if Storage is unreachable?

Working memory keeps decisions flowing for routine items. Anything novel gets queued until storage returns.

### What if a prediction is never resolved?

After 30 days past `expected_by` with no outcome match, mark as `unresolved` and log it as a calibration miss.

### What if the 30/80 target is missed?

If by day 30 the percentage of decisions hitting auto or one-tap is below 80%, the brain triggers a calibration mentoring session via Telegram. The session walks through the gap: which scopes failed to promote, why override rates were high, what foundation or heuristics need correcting. The brain does not extend the sprint thresholds beyond day 30 — it accepts the production thresholds and lets the owner course-correct in mentoring.

---

## Part 31 — Build order

When we sit down to write the Python code, build in this order. Each phase depends on the previous one.

**Note on ordering.** The phases below are the build order, not the read order. Distribution and the skill system (Phase -1) come first because everything else runs on top of them. Onboarding and ingestion (Phase 0) come last because they only need to exist once a real user is being onboarded; build them when the rest of the system is stable.

### Phase -1 — Distribution and skill engine (build first)

Before any orchestrator code, the runtime needs a place to live and the skill engine that everything else will plug into. Build this first.

- Hosted worker scaffold (Render or Railway deploy template, FastAPI, env var loader)
- Worker heartbeat endpoint (so the wizard can verify connection)
- Database migration runner (so worker startup creates and updates the full Supabase schema from Part 27, including skill engine tables)
- Skill engine: `loader.py`, `registry.py`, `runner.py`, `output_router.py`, `version_pinner.py`
- Workflow engine: `workflow_runner.py` for multi-skill chains
- One end-to-end test skill (a trivial echo skill) that proves: loader finds it, runner validates input/output, output goes to the declared destination, call is logged in `skill_calls`
- Skill registry seed at worker startup (read every system skill folder, register in the `skill_registry` table)
- Telegram `/skills` command and enable/disable handlers
- Desktop app shell (menu bar icon, "open wizard" action)
- Wizard skeleton (10 screens scaffolded but only Welcome and Connect to Claude functional)

### Phase 0 — Onboarding and ingestion (build last, used first)

These are the entry point for any new user. Build them after Phases 1-3 are stable so that when a user onboards, the live brain works on day one.

- Industry & business model selector (Stage 1 Step 1)
- Onboarding curriculum and session runner
- Foundation YAML writer
- Seed heuristic extraction from sessions
- The `industry-module-generator` skill (one skill that reads the user's industry profile and dynamically produces the follow-up curriculum, tested against at least 2-3 different sub-specialties)
- Ingestion pipeline (classify, chunk, embed, extract, mine, review)
- Owner review UI for ingestion findings

### Phase 1 — The basics (ship working version)

1. Project skeleton inside the worker (FastAPI, Postgres connection, env vars from worker host)
2. `RawEvent` model and Capture adapters (start with Gmail only)
3. Simple Orchestrator: classify, retrieve (semantic only), reason, log
4. Foundation YAML loader
5. The audit gate as a separate Claude call (loaded as a system skill from Part 24)
6. Decision logging to Postgres
7. **Telegram bot** for owner to receive suggestions and tap 1/2/3. This is the only owner interface. No web app.
8. **Conversation mode (Part 18).** Owner can message the bot freely, ask questions about decisions, give directives. Required for Phase 1 because directives in conversation are a major learning input.

This gets a working system end-to-end. No predict-before-reason yet, no working memory, no sleep cycle, no Whoop. But the owner can already run their business from Telegram and have conversations with Solomon.

### Phase 2 — Brain features

9. Salience scorer at intake
10. Predict-before-reason (System 1 + System 2)
11. Surprise score and divergence logging
12. Multi-lane retrieval
13. Working memory (Redis or Postgres TTL)
14. Memory decay at retrieval
15. **Whoop integration and owner state gate (Part 14)** — required before any user goes live, since Whoop gating is the safety valve for the compressed timeline

Now the brain is genuinely brain-like.

### Phase 3 — Sleep and prediction

16. Sleep cycle scheduler (one job at a time)
17. Surprise replay job (extended to include conversation review)
18. Rule archival job
19. Predictions table and checkpoint scheduler
20. Counterfactual generation and evaluation

### Phase 4 — Smarter learning

21. Stress test job
22. Conflict detection job
23. Skills vs facts split
24. Mentoring scheduler with gap analysis (delivered through Telegram)

### Phase 5 — Reports and polish

25. **Daily report generator (Part 19)** — replaces the morning digest for users with mature scopes
26. **Weekly report generator (Part 19)** — populates the reporting phase
27. **Issue and fix detectors (Part 19)** — feed both report types
28. **On-demand reports** — Solomon answers report-style questions in conversation
29. Autonomy ladder logic with sprint vs production thresholds and auto-promote/demote
30. Per-user isolation hardening
31. Failure modes and recovery
32. Observability (Langfuse for AI tracing, Sentry for errors)

### Phase 6 — Agent workforce (built once Phase 5 is stable)

33. **Paperclip integration scaffolding** — `paperclip/client.py`, `paperclip/poll.py`, `agent_projects` and `agent_activity_log` tables, basic Paperclip provisioning helper.
34. **`shape: project` classification** — extend the event classifier (Part 8) to mark project-shaped events. Conservative initially.
35. **`delegate-to-agent-workforce` skill** — Solomon's first concrete delegation skill. Tested with one default agent (e.g., a vendor coordinator).
36. **`paperclip-process-ticket-update` skill** — handles inbound activity from agents.
37. **`agent-callback-responder` skill** — answers `@solomon` mentions on tickets.
38. **`paperclip-hire-agent` skill** — proposes new agents to the owner via Telegram, creates them on approval.
39. **Agent workforce in reports** — daily and weekly report skills extended to include agent activity sections.
40. **Owner state gate applied to agent approvals** — red-band days escalate all agent-pending decisions.

This phase is built when at least one user has reached `act_alone` status on at least one scope (the trigger condition for offering the agent workforce). Until then, Phase 6 stays in backlog.

---

## Part 32 — Glossary

For when we forget what something means. Read this section first if a term in the rest of the document feels ambiguous — these are the rules.

### Names of the system

- **Solomon** — the **product** (codename). Used for the project, the brand, the company-facing name. Never used to mean a specific component.
- **The Brain** — synonym of Solomon when speaking about the system as a whole in narrative voice ("how the brain learns", "the brain forgets unused items"). Whole system, not any one part.

### Components (each one name)

- **Capture** — listens to the world (email, calls, Whoop, Telegram inbound, etc.).
- **Salience scorer** — rates how much an event matters.
- **The Conductor** *(= Orchestrator)* — the central routing function. The Python code that runs `process_event()` and calls every other component. Visual diagrams say "The Conductor"; spec and code say "Orchestrator". Same thing. The Conductor is **not** the Brain — it is one component within the Brain.
- **Claude** — the LLM. The Conductor calls Claude with different prompts for different jobs (System 1 prediction, System 2 reasoning, audit gate, mentoring questions).
- **Reasoning** — the Claude calls that produce a decision. Two passes: System 1 (fast, rules) and System 2 (slow, full context).
- **Owner state gate** — the Whoop-driven check that modulates today's effective autonomy ceiling. Static autonomy levels say what the brain has earned; the state gate says what it should actually do today given how the owner is showing up.
- **Audit gate** — the Claude call with an audit prompt that checks proposed actions before they ship. Returns approve, downgrade, reject, or request_rethink.
- **Storage** — where memories live. Working memory in Redis for hot context. Long-term storage in Supabase (Postgres + pgvector). Foundation files mirrored as YAML in the local desktop cache for fast boot..
- **Action layer** — the dispatcher that actually executes (sends emails, updates CRM, posts to Telegram).
- **Telegram bot** — the single owner interface. All inbound owner messages and outbound suggestions, digests, and mentoring sessions flow through it. There is no web app for daily use.
- **Sleep cycle** — the nightly jobs that consolidate the day.
- **Mentoring sessions** — scheduled Q&A with the owner, conducted through the Telegram bot.

### Active subject — who does what

When describing an action:
- The **Conductor** drives — sorts events, pulls memory, calls Claude, routes to the audit gate, asks the owner via Telegram.
- **Claude** outputs — generates the question, reasons about the decision.
- The **audit gate** judges — approves, downgrades, rejects, sends back for rethink.
- The **owner state gate** modulates — uses Whoop signals to set today's effective autonomy ceiling.
- The **Brain** / **Solomon** learns — system-level behavior in narrative voice.

### Concepts

- **The three phases** — Training (Phase 1, days 1-30), Approval (Phase 2, months 2-6), Reporting (Phase 3, month 6+). The owner's relationship with Solomon moves through them as the brain earns trust scope by scope. See Part 0.
- **The 30/80 target** — by day 30, 80% of daily decisions either ship without asking or land as a one-tap Telegram message. The Phase 1 success criterion.
- **Conversation mode** — free-form Telegram dialog between owner and Solomon. Available in all three phases. Both a way to use the brain and a way to train it. See Part 18.
- **Approval flow** — the one-tap and suggestion message mechanics that make up most of Phase 1 and Phase 2 interaction. See Part 17.
- **Reporting phase** — Phase 3 of the relationship. Daily and weekly reports replace one-tap approvals for scopes that reach `act_alone`. See Part 19.
- **Issue event / fix event** — automatically detected entries that populate the issues and fixes sections of reports. Defined in Part 19.
- **Salience** — how much an event matters.
- **System 1** — fast, rule-based prediction (a Claude Sonnet call with heuristics only).
- **System 2** — slow, reasoned answer (a Claude Opus call with full context).
- **Surprise** — gap between System 1 and System 2. Drives mentoring priority.
- **State band** — green / yellow / red. Computed from Whoop. Modulates autonomy.
- **Effective autonomy level** — the actual level used for an action today, after owner state gate modulation. May be lower than the static autonomy level for the scope.
- **Sprint mode** — the first 30 days. Lower promotion thresholds (20 decisions, <10% override, >0.7 confidence). After day 30, production thresholds take over.
- **Working memory** — fast cache of currently-active items.
- **Long-term memory** — Supabase (Postgres + pgvector). Foundation files mirrored as YAML in the local desktop cache for fast boot..
- **Heuristic** — a single rule. "If X, do Y."
- **Skill** — a multi-step playbook.
- **Foundation** — beliefs, principles, non-negotiables in YAML.
- **Autonomy ladder** — the four levels of trust per scope (watch, suggest, act with approval, act alone).
- **Counterfactual** — what we expected would happen if we had chosen differently.
- **Drift** — when old heuristics no longer match current reality.
- **Fragile** — a heuristic that failed a stress test or has a high override rate. Still active but downweighted.
- **Superseded** — an old version of a heuristic replaced by a new one. Kept for audit, never retrieved.
- **Regret signal** — evidence from counterfactuals that a different choice would have been better.
- **Onboarding** — the 30-day clone sprint that fills foundation files, mines historical heuristics, and gets the brain to 80% one-tap operation. See Part 4.
- **Ingestion** — the bulk and ad-hoc document pipeline. Separate from Capture. Processes historical artifacts.
- **Historical decision** — a decision extracted from an ingested document. Already happened, outcome already known.
- **Desktop app** — the small Mac or Windows application installed on the user's machine. Holds credentials and runs the setup wizard. Does not run any of the brain. See Part 2.
- **Hosted worker** — the per-user worker process running on Render or Railway. Always on. Runs the orchestrator, Telegram bot, sleep cycle, integrations, reports. See Part 2.
- **Wizard** — the browser-based setup flow that runs on the user's machine on first launch. 10 screens. See Part 3.
- **System skill** — a skill bundled with Solomon, shipped in the GitHub repo, updated with releases. Read-only at runtime. See Part 24.
- **User skill** — a skill learned by the brain or written by the user. Stored in the user's Supabase. Editable. See Part 24.
- **SKILL.md** — the prompt and instructions file at the root of every skill folder. Loaded as the system prompt when a skill is used.
- **Skill registry** — the in-memory and database index of every skill the orchestrator can call, with version metadata. Seeded at worker startup from bundled system skills, updated when user skills change. See Part 24.
- **Skill engine** — the code module that loads, validates, runs, and logs skills. Distinct from the orchestrator (which decides what to call) and from skills themselves (which do the work). See Part 24.
- **Skill contract** — the strict requirement that every skill declare an input schema, output schema, and output destination. Enforced at load time. See Part 24.
- **Workflow** — a multi-skill chain, defined as a YAML file. Versioned and edited like a skill. See Part 24.
- **Operation** — a multi-step process (onboarding session, mentoring session, sleep cycle, report) that pins skill versions while in flight. See Part 24.
- **Version pinning** — the rule that an in-flight operation locks to the skill version it started with, so a release mid-operation does not change behavior partway through. See Part 24.
- **BYO-cloud** — bring-your-own-cloud. The architecture pattern where the user owns every cloud account (Supabase, Redis, Render, Anthropic) and Solomon (the project) only ships software.
- **Paperclip** — open-source platform that orchestrates teams of AI agents like a company orchestrates employees. Solomon uses Paperclip to delegate multi-day jobs to agents while Solomon stays the user's only interface. See Part 26.
- **The agent workforce** — the team of Paperclip-managed AI agents that handle long-running, multi-step jobs on the user's behalf. Solomon is the Board; the agents are the employees; the owner sees everything through Solomon's Telegram bot.
- **Agent project** — a delegated multi-step job. Tracked as a Paperclip ticket and as a row in Solomon's `agent_projects` table.
- **Heartbeat (in Paperclip)** — the schedule on which an agent wakes to check its task queue and do work. Distinct from Solomon's near-real-time event handling.
- **Project-shape event** — an event whose work is multi-step and time-spanning (vendor sourcing, campaigns, lease negotiations). Classified as `shape: project` and routed to the agent workforce instead of the per-event action layer.

---

## Part 33 — How to read this document when building

Each Part above maps to a Python module:

- Part 5 → `capture/` (includes `capture/whoop.py` and `capture/telegram_inbound.py`)
- Part 6 → `salience/scorer.py`
- Part 7 → `orchestrator/main.py`
- Part 8 → `orchestrator/classify.py`
- Part 9 → `orchestrator/non_negotiables.py`
- Part 10 → `memory/working.py`
- Part 11 → `memory/retrieval.py`
- Part 12 → `reasoning/system_1.py`, `reasoning/system_2.py`, `reasoning/divergence.py`
- Part 13 → `audit_gate/audit.py`
- Part 15 → `autonomy/ladder.py`
- Part 14 → `state_gate/whoop_client.py`, `state_gate/band_calculator.py`, `state_gate/modulator.py`, `state_gate/state_log.py`
- Part 16 → `storage/decision_log.py`
- Part 20 → `predictions/checkpoints.py`, `predictions/counterfactuals.py`
- Part 21 → `mentoring/scheduler.py`, `mentoring/question_generator.py`
- Part 17 → `action/dispatcher.py`, `action/outbound/*.py`, `telegram/bot.py`, `telegram/outbound.py`, `telegram/approval_handler.py`, `telegram/command_handler.py`, `telegram/digest.py`
- Part 18 → `telegram/conversation.py`, `conversation/intent_classifier.py`, `conversation/responders/*.py`, `conversation/learning.py`
- Part 19 → `reports/daily.py`, `reports/weekly.py`, `reports/on_demand.py`, `reports/issue_detector.py`, `reports/fix_detector.py`, `reports/templates/`
- Part 22 → `sleep/replay.py`, `sleep/stress_test.py`, `sleep/archival.py`
- Part 27 → `storage/schema.sql`
- Part 28 → `users/isolation.py`
- Part 29 → `config/loader.py`
- Part 23 → `learning/confidence.py`, `mentoring/triggers.py`, `mentoring/proposals.py`, `mentoring/approval_flow.py`
- Part 4 → `onboarding/industry_selector.py`, `onboarding/curriculum.py`, `onboarding/telegram_session_runner.py`, `onboarding/foundation_writer.py`, `onboarding/seed_heuristics.py`, `onboarding/sprint_tracker.py`, `onboarding/industry_module_generator.py`
- Part 25 → `ingestion/upload_handler.py`, `ingestion/classifier.py`, `ingestion/chunker.py`, `ingestion/embedder.py`, `ingestion/extractor.py`, `ingestion/heuristic_miner.py`, `ingestion/cross_referencer.py`, `ingestion/sensitivity_filter.py`, `ingestion/review_queue.py`, `ingestion/budget_tracker.py`
- Part 2 → `worker/main.py`, `worker/health.py`, `desktop/main.py`, `desktop/credential_vault.py`, `desktop/upload_ui.py`, `infra/render-template.yaml`, `infra/migrations/`
- Part 3 → `wizard/server.py`, `wizard/screens/*.py`, `wizard/integrations/*.py`, `wizard/worker_provisioner.py`
- Part 24 → `skills/system/`, `workflows/`, `skill_engine/loader.py`, `skill_engine/registry.py`, `skill_engine/runner.py`, `skill_engine/workflow_runner.py`, `skill_engine/version_pinner.py`, `skill_engine/output_router.py`, `skill_engine/telegram_skill_index.py`, plus `skill_registry`, `skill_versions`, `skill_calls`, `operations`, `workflow_runs`, `user_skills` tables in Supabase
- Part 26 → `paperclip/client.py`, `paperclip/poll.py`, `paperclip/setup.py`, `agent_workforce/delegate.py`, `agent_workforce/agent_callback.py`, `agent_workforce/budget_monitor.py`, plus `agent_projects` and `agent_activity_log` tables in Supabase

The Orchestrator (Part 7) is the conductor. It calls each module in order. Each module is small, single-purpose, and testable on its own.

---

## End of document

This document is the source of truth for what we are building. Update it as we learn. Keep it readable.
