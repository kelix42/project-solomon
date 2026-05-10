"""Migration tests for the remaining interview-side skills.

Covers (parametrized over the migrated onboarding sessions):
- Session 01 (belief-system)
- Session 02 (why)
- Session 03 (principles)         (added in sub-batch 2)
- Session 04 (ideal-outcomes)     (added in sub-batch 2)
- Session 05 (non-negotiables)    (added in sub-batch 3)
- Session 06 (taxonomy)           (added in sub-batch 3)

And, non-parametrized (added in sub-batch 4):
- solomon-mentoring-session
- solomon-listening-agent

Each parametrized onboarding test mirrors the 12 cases that already pass for
Session 0 in tests/test_session_0_migration.py. The F1 to F4 query helpers and
the foundation YAML render are duplicated here (rather than imported) so each
test file stays self-contained and pytest collection does not require a
conftest.

Tests rely only on stdlib sqlite3 plus pytest and pyyaml (already CI deps).
"""

import json
import pathlib
import sqlite3
from datetime import datetime, timezone

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO / "db" / "schemas"
PROBE_LIBRARY_DIR = (
    REPO / "skills" / "interview" / "solomon-interview-engine" / "probe_library"
)
ONBOARDING_DIR = REPO / "skills" / "onboarding"

FORBIDDEN_LITERAL = [
    "You said",
    "I see",
    "Got it,",
    "Right.",
    "OK,",
    "Interesting",
    "That's a good point",
    "Tell me more",
    "Go on",
]
EM_DASH = chr(0x2014)


# ---- Per-session config (extended sub-batch by sub-batch) ----

SESSION_CONFIGS = {
    "01": {
        "domain": "belief-system",
        "foundation_path": "foundation/01-belief-system.yaml",
        "skill_dir": "solomon-onboarding-01-belief-system",
        "yaml_name": "belief-system.yaml",
        "required_field_ids": [
            "view_on_growth",
            "view_on_competition",
            "view_on_employee_relationship",
            "view_on_customer_relationship",
            "risk_appetite",
            "decision_speed_preference",
            "view_on_failure",
        ],
    },
    "02": {
        "domain": "why",
        "foundation_path": "foundation/02-why.yaml",
        "skill_dir": "solomon-onboarding-02-why",
        "yaml_name": "why.yaml",
        "required_field_ids": [
            "origin_story",
            "personal_motivation",
            "mission_or_change",
            "exit_horizon",
            "definition_of_success",
            "quit_conditions",
            "why_this_business_specifically",
        ],
    },
    "03": {
        "domain": "principles",
        "foundation_path": "foundation/03-principles.yaml",
        "skill_dir": "solomon-onboarding-03-principles",
        "yaml_name": "principles.yaml",
        "required_field_ids": [
            "principle_about_pricing",
            "principle_about_hiring_or_firing",
            "principle_about_customer_conflict",
            "principle_about_money",
            "principle_about_quality_vs_speed",
            "principle_about_saying_no",
            "principle_about_growth",
        ],
    },
    "04": {
        "domain": "ideal-outcomes",
        "foundation_path": "foundation/04-ideal-outcomes.yaml",
        "skill_dir": "solomon-onboarding-04-ideal-outcomes",
        "yaml_name": "ideal-outcomes.yaml",
        "required_field_ids": [
            "ideal_revenue_3_year",
            "ideal_team_size_3_year",
            "ideal_owner_workload_3_year",
            "ideal_customer_mix_3_year",
            "ideal_geographic_footprint_3_year",
            "one_year_milestone",
            "five_year_vision",
        ],
    },
    "05": {
        "domain": "non-negotiables",
        "foundation_path": "foundation/05-non-negotiables.yaml",
        "skill_dir": "solomon-onboarding-05-non-negotiables",
        "yaml_name": "non-negotiables.yaml",
        "required_field_ids": [
            "never_do_to_customers",
            "never_do_with_money",
            "never_do_with_employees",
            "never_do_with_partners_or_vendors",
            "never_do_with_competitors",
            "never_do_personally",
            "line_in_the_sand",
        ],
    },
    "06": {
        "domain": "scopes",
        "foundation_path": "foundation/06-scopes.yaml",
        "skill_dir": "solomon-onboarding-06-scopes",
        "yaml_name": "scopes.yaml",
        "required_field_ids": [
            "departments",
            "operational_scopes",
            "customer_segments_named",
        ],
    },
}


def session_param_ids():
    """Return the list of currently-active session keys for parametrization."""
    return sorted(SESSION_CONFIGS.keys())


# ---- Helpers (mirrored from tests/test_session_0_migration.py) ----

def make_temp_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for sql_file in sorted(SCHEMA_DIR.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    return conn


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_session(conn, session_id, status="active", domain="industry"):
    conn.execute(
        """
        INSERT INTO sessions
        (session_id, type, domain, status, started_at, last_activity_at, turns)
        VALUES (?, 'onboarding', ?, ?, ?, ?, 0)
        """,
        (session_id, domain, status, now_iso(), now_iso()),
    )
    conn.commit()


def make_capture(
    conn,
    session_id,
    source_turn,
    keywords,
    statement="captured statement",
    verbatim_phrase=None,
    type_="rule",
    confidence="stated",
    domain="industry",
    conflicts_with=None,
    capture_id=None,
):
    if capture_id is None:
        capture_id = (
            f"cap_{session_id}_{source_turn}_"
            f"{len(keywords)}_{statement[:8].replace(' ', '_')}"
        )
    conn.execute(
        """
        INSERT INTO captured_items
        (id, domain, type, statement, verbatim_phrase, conflicts_with,
         confidence, source_session, source_turn, keywords, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            capture_id,
            domain,
            type_,
            statement,
            verbatim_phrase or statement,
            json.dumps(conflicts_with) if conflicts_with else None,
            confidence,
            session_id,
            source_turn,
            json.dumps(keywords),
            now_iso(),
            now_iso(),
        ),
    )
    conn.commit()
    return capture_id


def f1_unfilled_required_fields(conn, session_id, field_ids):
    unfilled = []
    for fid in field_ids:
        row = conn.execute(
            """
            SELECT COUNT(*) AS filled
            FROM captured_items, json_each(captured_items.keywords) AS k
            WHERE captured_items.source_session = ?
              AND k.value = 'field:' || ?
            """,
            (session_id, fid),
        ).fetchone()
        if row["filled"] == 0:
            unfilled.append(fid)
    return unfilled


def f2_checkpoint_summary(conn, session_id):
    return conn.execute(
        """
        SELECT
          ci.id, ci.domain, ci.type, ci.statement, ci.verbatim_phrase,
          ci.confidence, ci.source_turn, ci.keywords, ci.conflicts_with,
          (
            SELECT k.value FROM json_each(ci.keywords) AS k
            WHERE k.value LIKE 'field:%' LIMIT 1
          ) AS required_field_tag
        FROM captured_items AS ci
        WHERE ci.source_session = ?
        ORDER BY ci.source_turn ASC, ci.id ASC
        """,
        (session_id,),
    ).fetchall()


def f3_render_foundation_yaml(conn, session_id, foundation_basename):
    """Compose foundation/NN-<domain>.yaml content from session captures."""
    required_rows = conn.execute(
        """
        SELECT k.value AS field_tag, ci.statement, ci.verbatim_phrase,
               ci.confidence, ci.source_turn
        FROM captured_items AS ci, json_each(ci.keywords) AS k
        WHERE ci.source_session = ?
          AND k.value LIKE 'field:%'
        ORDER BY ci.source_turn DESC
        """,
        (session_id,),
    ).fetchall()

    discovery_rows = conn.execute(
        """
        SELECT ci.statement, ci.verbatim_phrase, ci.example, ci.reasoning,
               ci.confidence, ci.keywords, ci.source_turn
        FROM captured_items AS ci
        WHERE ci.source_session = ?
          AND NOT EXISTS (
            SELECT 1 FROM json_each(ci.keywords) AS k WHERE k.value LIKE 'field:%'
          )
        ORDER BY ci.source_turn ASC
        """,
        (session_id,),
    ).fetchall()

    required_map = {}
    for row in required_rows:
        fid = row["field_tag"].split(":", 1)[1]
        if fid not in required_map:
            required_map[fid] = {
                "statement": row["statement"],
                "verbatim_phrase": row["verbatim_phrase"],
                "confidence": row["confidence"],
            }

    discovery_by_subtopic = {}
    for row in discovery_rows:
        keywords = json.loads(row["keywords"])
        subtopic = next(
            (k for k in keywords if not k.startswith("field:")), "other"
        )
        discovery_by_subtopic.setdefault(subtopic, []).append({
            "statement": row["statement"],
            "verbatim_phrase": row["verbatim_phrase"],
            "confidence": row["confidence"],
        })

    payload = {
        "last_updated": now_iso(),
        "required_fields": required_map,
        "discovery": discovery_by_subtopic,
        "voice_samples": [],
    }
    header = (
        f"# {foundation_basename}. Derived summary; canonical store is "
        "db/schemas/captured_items.sql.\n"
        "# Filled by the matching solomon-onboarding-NN-<domain> skill. "
        "Sleep-Cycle Job 12 (yaml-reconcile) catches drift; DB-wins.\n\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False)


def f4_turns_on_field(conn, session_id, field_id):
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT ci.source_turn) AS turns_on_field
        FROM captured_items AS ci, json_each(ci.keywords) AS k
        WHERE ci.source_session = ?
          AND k.value = 'field:' || ?
        """,
        (session_id, field_id),
    ).fetchone()
    return row["turns_on_field"]


def f5_write_scope_autonomy_from_session(conn, session_id):
    """Mirror Session 06 Stage E.3: for each operational_scopes captured row in
    this session, parse the JSON statement and INSERT OR IGNORE into
    scope_autonomy with level=0 and notes='source_session: <sid>'. Existing
    scope rows (already promoted by Sleep-Cycle Job 7) are preserved.
    Returns the count of rows actually inserted."""
    rows = conn.execute(
        """
        SELECT ci.statement
        FROM captured_items AS ci, json_each(ci.keywords) AS k
        WHERE ci.source_session = ?
          AND k.value = 'field:operational_scopes'
        """,
        (session_id,),
    ).fetchall()
    written = 0
    for row in rows:
        try:
            scope_data = json.loads(row["statement"])
            scope_name = scope_data.get("name")
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
        if not scope_name:
            continue
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO scope_autonomy
              (scope, level, since, last_reeval_at, notes)
            VALUES (?, 0, ?, ?, ?)
            """,
            (scope_name, now_iso(), now_iso(), f"source_session: {session_id}"),
        )
        written += cursor.rowcount
    conn.commit()
    return written


def session_status(conn, session_num, required_field_ids):
    """Mirror the migrated-sessions check in solomon-onboarding-status."""
    prefix = f"onboarding-{session_num}-%"
    row = conn.execute(
        """
        SELECT session_id, status
        FROM sessions
        WHERE session_id LIKE ?
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (prefix,),
    ).fetchone()
    if row is None:
        return ("not_started", len(required_field_ids))
    unfilled = f1_unfilled_required_fields(
        conn, row["session_id"], required_field_ids
    )
    if row["status"] == "complete" and not unfilled:
        return ("complete", 0)
    return ("in_progress", len(unfilled))


# ---- Fixtures ----

@pytest.fixture
def db():
    conn = make_temp_db()
    yield conn
    conn.close()


@pytest.fixture
def session_config(request):
    return SESSION_CONFIGS[request.param]


# ---- Parametrized onboarding tests ----

@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_session_creates_row(db, session_config):
    sid = f"onboarding-{[k for k, v in SESSION_CONFIGS.items() if v is session_config][0]}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    row = db.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (sid,)
    ).fetchone()
    assert row is not None
    assert row["status"] == "active"
    assert row["type"] == "onboarding"
    assert row["domain"] == session_config["domain"]


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_discovery_writes_captures(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    make_capture(db, sid, source_turn=1, keywords=["sample-keyword"],
                 statement="discovery capture A",
                 domain=session_config["domain"])
    make_capture(db, sid, source_turn=2, keywords=["another-keyword"],
                 statement="discovery capture B",
                 domain=session_config["domain"])
    rows = db.execute(
        "SELECT * FROM captured_items WHERE source_session = ? ORDER BY source_turn",
        (sid,),
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["domain"] == session_config["domain"]


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_required_fields_query(db, session_config):
    """Exercises 0 / 3 / all 7 filled states for F1."""
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fids = session_config["required_field_ids"]

    assert f1_unfilled_required_fields(db, sid, fids) == fids

    for i, fid in enumerate(fids[:3]):
        make_capture(db, sid, source_turn=i + 1,
                     keywords=[f"field:{fid}"],
                     statement=f"answer {fid}",
                     domain=session_config["domain"])
    assert f1_unfilled_required_fields(db, sid, fids) == fids[3:]

    for i, fid in enumerate(fids[3:]):
        make_capture(db, sid, source_turn=i + 4,
                     keywords=[f"field:{fid}"],
                     statement=f"answer {fid}",
                     domain=session_config["domain"])
    assert f1_unfilled_required_fields(db, sid, fids) == []


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_required_field_decline(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fid = session_config["required_field_ids"][-1]
    make_capture(
        db, sid, source_turn=1,
        keywords=[f"field:{fid}"],
        statement="I don't know",
        type_="preference",
        domain=session_config["domain"],
    )
    unfilled = f1_unfilled_required_fields(
        db, sid, session_config["required_field_ids"]
    )
    assert fid not in unfilled


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_session_cannot_complete_without_required_fields(db, session_config):
    """Generalized to any session size: fill all but one required field on a
    session marked status='complete' and assert the status check still reports
    in_progress with remaining=1."""
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, status="complete", domain=session_config["domain"])
    fids = session_config["required_field_ids"]
    fill_count = len(fids) - 1
    for i, fid in enumerate(fids[:fill_count]):
        make_capture(db, sid, source_turn=i + 1,
                     keywords=[f"field:{fid}"],
                     statement=f"answer {fid}",
                     domain=session_config["domain"])
    state, remaining = session_status(db, num, fids)
    assert state == "in_progress"
    assert remaining == 1


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_two_turn_cap_enforced(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fid = session_config["required_field_ids"][-1]

    make_capture(db, sid, source_turn=1,
                 keywords=[f"field:{fid}", "follow-up-keyword"],
                 statement="initial answer",
                 domain=session_config["domain"])
    assert f4_turns_on_field(db, sid, fid) == 1

    make_capture(db, sid, source_turn=2,
                 keywords=[f"field:{fid}", "follow-up-keyword"],
                 statement="follow-up answer",
                 domain=session_config["domain"])
    assert f4_turns_on_field(db, sid, fid) == 2

    cap_blocks_followup = f4_turns_on_field(db, sid, fid) >= 2
    assert cap_blocks_followup is True

    unfilled = f1_unfilled_required_fields(
        db, sid, session_config["required_field_ids"]
    )
    assert fid not in unfilled


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_closing_checkpoint_summary(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fid = session_config["required_field_ids"][0]
    make_capture(db, sid, source_turn=1, keywords=["sample-keyword"],
                 statement="discovery row",
                 domain=session_config["domain"])
    make_capture(db, sid, source_turn=2,
                 keywords=[f"field:{fid}", "sample-keyword"],
                 statement="required-field row",
                 domain=session_config["domain"])
    rows = f2_checkpoint_summary(db, sid)
    assert len(rows) == 2
    assert rows[0]["required_field_tag"] is None
    assert rows[1]["required_field_tag"] == f"field:{fid}"


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_owner_correction_at_checkpoint(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    prior_id = make_capture(
        db, sid, source_turn=1,
        keywords=["sample-keyword"],
        statement="initial statement",
        domain=session_config["domain"],
    )
    make_capture(
        db, sid, source_turn=2,
        keywords=["sample-keyword"],
        statement="corrected statement",
        conflicts_with=[prior_id],
        domain=session_config["domain"],
    )
    rows = f2_checkpoint_summary(db, sid)
    assert len(rows) == 2
    new_conflicts = json.loads(rows[1]["conflicts_with"])
    assert prior_id in new_conflicts


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_yaml_render_at_close(db, session_config):
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fids = session_config["required_field_ids"]
    for i, fid in enumerate(fids):
        make_capture(db, sid, source_turn=i + 1,
                     keywords=[f"field:{fid}"],
                     statement=f"answer for {fid}",
                     domain=session_config["domain"])
    make_capture(db, sid, source_turn=99, keywords=["sample-keyword"],
                 statement="discovery extra",
                 domain=session_config["domain"])

    foundation_basename = pathlib.Path(session_config["foundation_path"]).name
    rendered = f3_render_foundation_yaml(db, sid, foundation_basename)
    assert rendered.startswith(f"# {foundation_basename}.")

    payload = yaml.safe_load(rendered)
    assert "last_updated" in payload
    assert "required_fields" in payload
    assert "discovery" in payload
    assert "voice_samples" in payload
    assert set(payload["required_fields"].keys()) == set(fids)
    assert "sample-keyword" in payload["discovery"]


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_no_opt_data_writes(session_config):
    skill_path = ONBOARDING_DIR / session_config["skill_dir"] / "SKILL.md"
    body = skill_path.read_text(encoding="utf-8")
    assert "/opt/data/" not in body, (
        f"{session_config['skill_dir']} should not reference /opt/data/."
    )


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_status_skill_reports_in_progress(db, session_config):
    """Generalized to any session size: starts at remaining=len(fids), fills
    all but one, ends at remaining=1."""
    num = [k for k, v in SESSION_CONFIGS.items() if v is session_config][0]
    sid = f"onboarding-{num}-2026-05-10"
    make_session(db, sid, domain=session_config["domain"])
    fids = session_config["required_field_ids"]
    state, remaining = session_status(db, num, fids)
    assert state == "in_progress"
    assert remaining == len(fids)

    fill_count = len(fids) - 1
    for i, fid in enumerate(fids[:fill_count]):
        make_capture(db, sid, source_turn=i + 1,
                     keywords=[f"field:{fid}"],
                     statement=f"answer {fid}",
                     domain=session_config["domain"])
    state, remaining = session_status(db, num, fids)
    assert state == "in_progress"
    assert remaining == 1


@pytest.mark.parametrize("session_config", session_param_ids(), indirect=True)
def test_probe_template_no_chatbot_patterns(session_config):
    """Static lint: every probe template, fallback, and required_field prompt
    must be free of the listed chatbot filler patterns and must contain no
    em dash characters. The probe_style block is documentation and may quote
    forbidden patterns as anti-examples; intentionally excluded from the scan."""
    yaml_path = PROBE_LIBRARY_DIR / session_config["yaml_name"]
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    targets = []
    for kw, entries in data.get("keywords", {}).items():
        for entry in entries:
            targets.append((f"keywords.{kw}", entry["template"]))
    for i, fb in enumerate(data.get("fallbacks", [])):
        targets.append((f"fallbacks[{i}]", fb))
    for rf in data.get("required_fields", []):
        targets.append((f"required_fields[{rf['id']}].prompt", rf["prompt"]))

    failures = []
    for label, text in targets:
        for pat in FORBIDDEN_LITERAL:
            if pat in text:
                failures.append((label, pat, text))
        if EM_DASH in text:
            failures.append((label, "em-dash", text))
    assert not failures, f"chatbot pattern violations: {failures}"


# ---- Non-parametrized: Session 05 hard-rule promotion ----

def f3_render_non_negotiables_yaml(
    conn, session_id, existing_rules, pending_promotions
):
    """Session 05 special render. Composes the full foundation/05-non-negotiables.yaml
    body: standard prose blocks (last_updated, required_fields, discovery,
    voice_samples) PLUS a rules: block built from the existing rules (preserved
    across renders) appended with this session's pending_promotions.

    pending_promotions: list of dicts with keys
      id, statement, domain, condition, on_violate.
    """
    required_rows = conn.execute(
        """
        SELECT k.value AS field_tag, ci.statement, ci.verbatim_phrase,
               ci.confidence, ci.source_turn
        FROM captured_items AS ci, json_each(ci.keywords) AS k
        WHERE ci.source_session = ?
          AND k.value LIKE 'field:%'
        ORDER BY ci.source_turn DESC
        """,
        (session_id,),
    ).fetchall()

    discovery_rows = conn.execute(
        """
        SELECT ci.statement, ci.verbatim_phrase, ci.example, ci.reasoning,
               ci.confidence, ci.keywords, ci.source_turn
        FROM captured_items AS ci
        WHERE ci.source_session = ?
          AND NOT EXISTS (
            SELECT 1 FROM json_each(ci.keywords) AS k WHERE k.value LIKE 'field:%'
          )
        ORDER BY ci.source_turn ASC
        """,
        (session_id,),
    ).fetchall()

    required_map = {}
    for row in required_rows:
        fid = row["field_tag"].split(":", 1)[1]
        if fid not in required_map:
            required_map[fid] = {
                "statement": row["statement"],
                "verbatim_phrase": row["verbatim_phrase"],
                "confidence": row["confidence"],
            }

    discovery_by_subtopic = {}
    for row in discovery_rows:
        keywords = json.loads(row["keywords"])
        subtopic = next(
            (k for k in keywords if not k.startswith("field:")
             and k != "hard_rule_promoted"),
            "other",
        )
        discovery_by_subtopic.setdefault(subtopic, []).append({
            "statement": row["statement"],
            "verbatim_phrase": row["verbatim_phrase"],
            "confidence": row["confidence"],
        })

    merged_rules = list(existing_rules) + list(pending_promotions)

    payload = {
        "last_updated": now_iso(),
        "required_fields": required_map,
        "discovery": discovery_by_subtopic,
        "voice_samples": [],
        "rules": merged_rules,
    }
    header = (
        "# 05-non-negotiables.yaml. Derived summary; canonical store is "
        "db/schemas/captured_items.sql.\n"
        "# rules: block holds the §1 hard-rule schema entries enforced by "
        "Stage 4 of the §2.2.5 pipeline.\n"
        "# Filled by solomon-onboarding-05-non-negotiables and by "
        "solomon-mentoring-session promotions.\n\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False)


def mark_promoted(conn, capture_id):
    """Append 'hard_rule_promoted' to the row's keywords JSON array."""
    row = conn.execute(
        "SELECT keywords FROM captured_items WHERE id = ?", (capture_id,)
    ).fetchone()
    keywords = json.loads(row["keywords"])
    if "hard_rule_promoted" not in keywords:
        keywords.append("hard_rule_promoted")
    conn.execute(
        "UPDATE captured_items SET keywords = ?, updated_at = ? WHERE id = ?",
        (json.dumps(keywords), now_iso(), capture_id),
    )
    conn.commit()


def test_session_05_hard_rule_promotion(db, tmp_path):
    """Session 05 closing checkpoint extension:
    - Two captured non-negotiables exist.
    - Owner promotes ONE of them to a hard rule (the other stays in captured_items only).
    - F3 render produces foundation/05-non-negotiables.yaml with:
      - the standard prose blocks present
      - a rules: block containing exactly the one promoted rule
      - the promoted rule has the §1 schema fields
    - Both captured_items rows persist in the DB after render.
    """
    sid = "onboarding-05-2026-05-10"
    make_session(db, sid, domain="non-negotiables")

    promoted_id = make_capture(
        db, sid, source_turn=1,
        keywords=["field:never_do_to_customers"],
        statement="Never sell something the customer cannot use.",
        verbatim_phrase="Never sell something the customer cannot use.",
        domain="non-negotiables",
    )
    skipped_id = make_capture(
        db, sid, source_turn=2,
        keywords=["field:never_do_with_money"],
        statement="Never go below 60 days of runway.",
        verbatim_phrase="Never go below 60 days of runway.",
        domain="non-negotiables",
    )

    # Owner confirms promotion of the first; skips the second.
    mark_promoted(db, promoted_id)
    pending_promotions = [{
        "id": promoted_id,
        "statement": "Never sell something the customer cannot use.",
        "domain": "non-negotiables",
        "condition": {
            "and": [
                {"==": [{"var": "event.classification.scope"}, "customer"]},
                {"==": [{"var": "event.classification.decision_type"}, "sell_to_customer"]},
                {"==": [{"var": "event.payload.customer_can_use"}, False]},
            ],
        },
        "on_violate": {
            "action": "REJECT",
            "explanation": (
                "Selling to a customer who cannot use the product violates "
                f"a non-negotiable. See captured_items.id {promoted_id}."
            ),
        },
    }]

    # No prior rules exist in this fresh test scenario.
    existing_rules = []

    rendered = f3_render_non_negotiables_yaml(
        db, sid, existing_rules, pending_promotions
    )

    # Write to a tmp path so we can re-parse and inspect.
    out_path = tmp_path / "05-non-negotiables.yaml"
    out_path.write_text(rendered, encoding="utf-8")

    payload = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert "last_updated" in payload
    assert "required_fields" in payload
    assert "discovery" in payload
    assert "voice_samples" in payload
    assert "rules" in payload

    # Exactly one promoted rule.
    assert len(payload["rules"]) == 1
    rule = payload["rules"][0]
    assert rule["id"] == promoted_id
    assert rule["domain"] == "non-negotiables"
    assert rule["statement"] == "Never sell something the customer cannot use."
    assert "condition" in rule
    assert "and" in rule["condition"]
    assert "on_violate" in rule
    assert rule["on_violate"]["action"] == "REJECT"
    assert promoted_id in rule["on_violate"]["explanation"]

    # Both captured_items rows persist; only the promoted one carries the marker.
    rows = db.execute(
        "SELECT id, keywords FROM captured_items WHERE source_session = ? ORDER BY source_turn",
        (sid,),
    ).fetchall()
    assert len(rows) == 2
    promoted_keywords = json.loads(rows[0]["keywords"])
    skipped_keywords = json.loads(rows[1]["keywords"])
    assert "hard_rule_promoted" in promoted_keywords
    assert "hard_rule_promoted" not in skipped_keywords


def test_session_05_hard_rule_render_preserves_existing_rules(db, tmp_path):
    """If foundation/05-non-negotiables.yaml already had rules from a prior
    session (or mentoring promotion), the Session 05 render must preserve them
    and append the new ones. Validates the merge step in Stage E."""
    sid = "onboarding-05-2026-05-10"
    make_session(db, sid, domain="non-negotiables")

    new_capture_id = make_capture(
        db, sid, source_turn=1,
        keywords=["field:never_do_with_money"],
        statement="Never go below 60 days of runway.",
        verbatim_phrase="Never go below 60 days of runway.",
        domain="non-negotiables",
    )
    mark_promoted(db, new_capture_id)

    existing_rules = [{
        "id": "01HX0PRIORRULEID",
        "statement": "Never quote below cost+15% on commercial jobs.",
        "domain": "pricing",
        "condition": {
            "and": [
                {"==": [{"var": "event.classification.scope"}, "pricing"]},
                {"<": [{"var": "event.payload.margin_pct"}, 15]},
            ],
        },
        "on_violate": {
            "action": "REJECT",
            "explanation": "Below 15% margin on commercial work.",
        },
    }]

    pending_promotions = [{
        "id": new_capture_id,
        "statement": "Never go below 60 days of runway.",
        "domain": "non-negotiables",
        "condition": {
            "and": [
                {"==": [{"var": "event.classification.scope"}, "finance"]},
                {"<": [{"var": "event.payload.runway_days"}, 60]},
            ],
        },
        "on_violate": {
            "action": "REJECT",
            "explanation": (
                "Going below 60 days of runway violates a non-negotiable. "
                f"See captured_items.id {new_capture_id}."
            ),
        },
    }]

    rendered = f3_render_non_negotiables_yaml(
        db, sid, existing_rules, pending_promotions
    )
    out_path = tmp_path / "05-non-negotiables.yaml"
    out_path.write_text(rendered, encoding="utf-8")

    payload = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert len(payload["rules"]) == 2
    rule_ids = [r["id"] for r in payload["rules"]]
    assert "01HX0PRIORRULEID" in rule_ids
    assert new_capture_id in rule_ids


# ---- Non-parametrized: Session 06 scope_autonomy write ----

def test_session_06_writes_scope_autonomy(db):
    """Session 06 Stage E.3: for each operational_scopes captured row, parse
    the JSON statement {name, department} and INSERT OR IGNORE into
    db.scope_autonomy with level=0 and notes='source_session: <sid>'.

    Validates four properties:
    1. New scopes are inserted at level=0 with source_session in notes.
    2. department-null scopes are still written (department lives in
       captured_items only, not in scope_autonomy).
    3. Pre-existing scope_autonomy rows (already promoted by Sleep-Cycle
       Job 7) are preserved by INSERT OR IGNORE.
    4. Re-running the write is idempotent (no duplicate rows).
    """
    sid = "onboarding-06-2026-05-10"
    make_session(db, sid, domain="scopes")

    # Three operational_scopes captures, statement is JSON {name, department}.
    make_capture(
        db, sid, source_turn=1,
        keywords=["field:operational_scopes"],
        statement=json.dumps({
            "name": "respond_to_inbound_lead",
            "department": "Sales",
        }),
        domain="scopes",
    )
    make_capture(
        db, sid, source_turn=2,
        keywords=["field:operational_scopes"],
        statement=json.dumps({
            "name": "send_invoice",
            "department": "Finance",
        }),
        domain="scopes",
    )
    make_capture(
        db, sid, source_turn=3,
        keywords=["field:operational_scopes"],
        statement=json.dumps({
            "name": "draft_proposal",
            "department": None,
        }),
        domain="scopes",
    )

    # Pre-existing scope_autonomy row (already promoted by Sleep-Cycle Job 7).
    db.execute(
        """
        INSERT INTO scope_autonomy (scope, level, since, last_reeval_at, notes)
        VALUES (?, 2, ?, ?, ?)
        """,
        ("respond_to_inbound_lead", now_iso(), now_iso(), "promoted by Job 7"),
    )
    db.commit()

    # First run: send_invoice and draft_proposal are new; the other is preserved.
    written = f5_write_scope_autonomy_from_session(db, sid)
    assert written == 2

    rows = db.execute(
        "SELECT scope, level, notes FROM scope_autonomy ORDER BY scope"
    ).fetchall()
    by_scope = {r["scope"]: r for r in rows}

    assert set(by_scope.keys()) == {
        "respond_to_inbound_lead",
        "send_invoice",
        "draft_proposal",
    }

    # Property 3: pre-existing row preserved.
    assert by_scope["respond_to_inbound_lead"]["level"] == 2
    assert by_scope["respond_to_inbound_lead"]["notes"] == "promoted by Job 7"

    # Property 1: new scopes at level=0 with source_session in notes.
    assert by_scope["send_invoice"]["level"] == 0
    assert sid in by_scope["send_invoice"]["notes"]

    # Property 2: department-null scope still written (department not in schema).
    assert by_scope["draft_proposal"]["level"] == 0
    assert sid in by_scope["draft_proposal"]["notes"]

    # Property 4: idempotent re-run.
    written_again = f5_write_scope_autonomy_from_session(db, sid)
    assert written_again == 0
    final_count = db.execute(
        "SELECT COUNT(*) AS n FROM scope_autonomy"
    ).fetchone()["n"]
    assert final_count == 3
