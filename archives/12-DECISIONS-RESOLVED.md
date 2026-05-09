# Solomon Spec — The 12 Open Questions, Resolved

Resolved during the open-question pass that produced spec v1.0 (May 6, 2026).
Each entry: the question, the chosen option, and the one-line rationale.
Full reasoning is preserved in solomon-spec-v1.0.md.

───────────────────────────────────────────────────────────────
Q1. Distribution model — how does a new user install Solomon?
───────────────────────────────────────────────────────────────
CHOSEN: Hermes-native skill pack, installed via git clone + setup wizard.
WHY:    No mandatory external services. Solomon runs entirely on the user's
        own Hermes instance. Setup wizard handles config, DB init, and
        first-run onboarding handoff.

───────────────────────────────────────────────────────────────
Q2. Storage architecture — where does Solomon's state live?
───────────────────────────────────────────────────────────────
CHOSEN: 3-tier storage.
        - Memory  → small, hot, always-injected facts (preferences, identity)
        - Skills  → procedural knowledge + onboarding artifacts (YAML profile)
        - SQLite  → structured records (decisions, audit logs, mentoring history)
WHY:    Each tier matches a distinct access pattern. Avoids overloading
        Memory (which has a hard char cap) and avoids putting volatile
        records in Skills (which is meant for procedures).

───────────────────────────────────────────────────────────────
Q3. Scope taxonomy — how are decisions categorized?
───────────────────────────────────────────────────────────────
CHOSEN: 2-level taxonomy.
        - Fixed scopes:        Personal / Business / Strategic
        - User-defined scopes: anything the owner adds during onboarding
WHY:    Fixed scopes cover the universal categories every owner has;
        user-defined allows specialization (e.g. "Real Estate", "Law Firm
        AI Practice") without bloating the core schema.

───────────────────────────────────────────────────────────────
Q4. Audit model — how is each Solomon decision validated?
───────────────────────────────────────────────────────────────
CHOSEN: 2-layer audit.
        - Hard Gate (Structured): JSONLogic rules — deterministic,
          fast, blocks anything that violates non-negotiables.
        - Soft Gate (LLM):        Free-form review — catches subtle
          misalignment with principles, beliefs, ideal outcomes.
WHY:    Hard gate is cheap and absolute. Soft gate catches things rules
        can't express. Both must pass for Solomon to act unilaterally.

───────────────────────────────────────────────────────────────
Q5. Biometric integration — how does Solomon read owner state?
───────────────────────────────────────────────────────────────
CHOSEN: Per-stakes biometric ceilings, with 28-day personal calibration.
WHY:    Owner's "tired" baseline is unique to them. First 28 days establish
        personal HRV/sleep/stress norms; after that, ceilings tighten or
        loosen actions based on stakes (low/med/high) vs. current state.

───────────────────────────────────────────────────────────────
Q6. Sub-agent lifecycle — how do specialized agents get created?
───────────────────────────────────────────────────────────────
CHOSEN: Ephemeral by default; promote to persistent profile on recurring volume.
WHY:    Avoids profile bloat. Most sub-tasks are one-offs; only when
        Solomon sees the same kind of task repeatedly does it propose
        formalizing a persistent sub-agent profile.

───────────────────────────────────────────────────────────────
Q7. Mentoring trigger — when does Solomon initiate a mentoring session?
───────────────────────────────────────────────────────────────
CHOSEN: Gap-driven, with floor/ceiling guards.
        - Floor:  minimum cadence (so owner isn't ignored for too long)
        - Ceiling: maximum cadence (so owner isn't pestered)
WHY:    Pure event-driven would either spam or starve. Floor/ceiling
        bounds it; gaps in profile coverage prioritize what to discuss.

───────────────────────────────────────────────────────────────
Q8. Hosting model — does the owner self-host or use a hosted instance?
───────────────────────────────────────────────────────────────
CHOSEN: Per-scope hosting.
        - Personal scope:           local only
        - Business/Strategic scope: hosted allowed
WHY:    Personal data never leaves the owner's machine. Business workflows
        often need cloud integrations (calendars, CRMs, email) so hosted
        is permitted there.

───────────────────────────────────────────────────────────────
Q9. Decision-log retrieval — how does Solomon find past decisions?
───────────────────────────────────────────────────────────────
CHOSEN: Hybrid retrieval.
        - Recency:    recent decisions weighted up
        - Relevance:  semantic match on current context
        - Correction: decisions the owner overrode get extra weight
                      (so Solomon doesn't repeat corrected mistakes)
WHY:    Pure recency forgets old patterns. Pure relevance misses temporal
        context. Correction-weighting is the single biggest lever for
        Solomon to actually learn from the owner.

───────────────────────────────────────────────────────────────
Q10. Backup / portability — how is Solomon state exported?
───────────────────────────────────────────────────────────────
CHOSEN: JSONL export bundles.
WHY:    Line-delimited JSON is diff-friendly, streamable, and trivial to
        import into another Solomon instance or analyze externally.
        Bundle = profile YAML + decisions JSONL + audit JSONL + skills tarball.

───────────────────────────────────────────────────────────────
Q11. Conflict resolution — what happens when profile YAML and inferred
     rules disagree?
───────────────────────────────────────────────────────────────
CHOSEN: Profile-wins enforcement, but contradiction is surfaced.
WHY:    Owner's explicit declarations always override inferred patterns.
        But the contradiction is logged and raised in the next mentoring
        session so the owner can decide whether to update the profile or
        the inferred rule.

───────────────────────────────────────────────────────────────
Q12. Schema evolution — how do future spec changes propagate?
───────────────────────────────────────────────────────────────
CHOSEN: Versioned spec bumps + migration files under solomon/migrations/.
WHY:    Same pattern as database migrations. Each schema change ships
        with a forward migration so existing owner data survives upgrades.
