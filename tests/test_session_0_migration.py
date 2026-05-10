"""Session 0 migration tests.

Validates the Style A to Style B migration of solomon-onboarding-00-industry:
the industry.yaml schema (probe_style, required_fields, keywords, fallbacks),
DB-backed session and required-field tracking, the five-stage flow contracts
(setup, discovery, required-fields pass, closing checkpoint, close), and the
status skill reporting "in progress" vs "complete" using DB state.

Tests use only stdlib sqlite3 plus pytest and pyyaml (already CI dependencies).
The F1 to F4 query helpers below mirror the SQL documented in the migrated
skill body. The test render of foundation/00-industry.yaml is a faithful
implementation of the F3 contract; production rendering happens inside a
Hermes agent session and is not part of this test surface.
"""

import json
import pathlib
import sqlite3
from datetime import datetime, timezone

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO / "db" / "schemas"
INDUSTRY_YAML = (
    REPO
    / "skills"
    / "interview"
    / "solomon-interview-engine"
    / "probe_library"
    / "industry.yaml"
)
SESSION_0_SKILL = (
    REPO
    / "skills"
    / "onboarding"
    / "solomon-onboarding-00-industry"
    / "SKILL.md"
)

REQUIRED_FIELD_IDS_EXPECTED = [
    "business_category",
    "primary_product_or_service",
    "customer_orientation",
    "geographic_scope",
    "revenue_model",
    "growth_stage",
    "concentration_risk",
]

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
EM_DASH = chr(0x2014)  # constructed via chr() so the source file stays em-dash-free


# ----- helpers -----

def make_temp_db():
    """Build an in-memory SQLite database from db/schemas/*.sql."""
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
    """Insert a captured_items row, mocking what solomon-extraction would write."""
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


# ----- F1, F2, F3, F4 implementations under test -----

def f1_unfilled_required_fields(conn, session_id, field_ids):
    """Return ordered list of required_field ids not yet filled for this session."""
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
          ci.id,
          ci.domain,
          ci.type,
          ci.statement,
          ci.verbatim_phrase,
          ci.confidence,
          ci.source_turn,
          ci.keywords,
          ci.conflicts_with,
          (
            SELECT k.value
            FROM json_each(ci.keywords) AS k
            WHERE k.value LIKE 'field:%'
            LIMIT 1
          ) AS required_field_tag
        FROM captured_items AS ci
        WHERE ci.source_session = ?
        ORDER BY ci.source_turn ASC, ci.id ASC
        """,
        (session_id,),
    ).fetchall()


def f3_render_foundation_yaml(conn, session_id):
    """Compose foundation/00-industry.yaml content from session captures."""
    required_rows = conn.execute(
        """
        SELECT k.value AS field_tag,
               ci.statement,
               ci.verbatim_phrase,
               ci.confidence,
               ci.source_turn
        FROM captured_items AS ci, json_each(ci.keywords) AS k
        WHERE ci.source_session = ?
          AND k.value LIKE 'field:%'
        ORDER BY ci.source_turn DESC
        """,
        (session_id,),
    ).fetchall()

    discovery_rows = conn.execute(
        """
        SELECT ci.statement,
               ci.verbatim_phrase,
               ci.example,
               ci.reasoning,
               ci.confidence,
               ci.keywords,
               ci.source_turn
        FROM captured_items AS ci
        WHERE ci.source_session = ?
          AND NOT EXISTS (
            SELECT 1 FROM json_each(ci.keywords) AS k WHERE k.value LIKE 'field:%'
          )
        ORDER BY ci.source_turn ASC
        """,
        (session_id,),
    ).fetchall()

    # Latest-turn-wins per required field.
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
        "voice_samples": [],  # vocab join elided in test render
    }
    header = (
        "# 00-industry.yaml. Derived summary; canonical store is "
        "db/schemas/captured_items.sql.\n"
        "# Topics: industry / sector / geography / customers / "
        "ecosystem / risks / trends.\n"
        "# Filled by solomon-onboarding-00-industry. Sleep-Cycle "
        "Job 12 (yaml-reconcile) catches drift; DB-wins.\n\n"
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


def session_0_status(conn):
    """Mirror the Session 0 status check in solomon-onboarding-status SKILL.md."""
    row = conn.execute(
        """
        SELECT session_id, status
        FROM sessions
        WHERE session_id LIKE 'onboarding-00-%'
        ORDER BY started_at DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return ("not_started", 7)
    unfilled = f1_unfilled_required_fields(
        conn, row["session_id"], REQUIRED_FIELD_IDS_EXPECTED
    )
    if row["status"] == "complete" and not unfilled:
        return ("complete", 0)
    return ("in_progress", len(unfilled))


# ----- fixtures -----

@pytest.fixture
def db():
    conn = make_temp_db()
    yield conn
    conn.close()


@pytest.fixture
def industry_yaml():
    with open(INDUSTRY_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----- tests -----

def test_session_creates_row(db):
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    row = db.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (sid,)
    ).fetchone()
    assert row is not None
    assert row["status"] == "active"
    assert row["type"] == "onboarding"
    assert row["domain"] == "industry"


def test_discovery_writes_captures(db):
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    make_capture(db, sid, source_turn=1, keywords=["product"],
                 statement="custom millwork")
    make_capture(db, sid, source_turn=2, keywords=["customer-mix"],
                 statement="60 percent residential")
    rows = db.execute(
        "SELECT * FROM captured_items WHERE source_session = ? ORDER BY source_turn",
        (sid,),
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["domain"] == "industry"
    assert rows[0]["statement"] == "custom millwork"


def test_required_fields_query(db):
    """Exercises 0 filled, 3 filled, and all 7 filled states for F1."""
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)

    # Zero filled.
    assert (
        f1_unfilled_required_fields(db, sid, REQUIRED_FIELD_IDS_EXPECTED)
        == REQUIRED_FIELD_IDS_EXPECTED
    )

    # Three filled.
    for i, fid in enumerate(REQUIRED_FIELD_IDS_EXPECTED[:3]):
        make_capture(
            db, sid, source_turn=i + 1,
            keywords=[f"field:{fid}"], statement=f"answer {fid}",
        )
    assert (
        f1_unfilled_required_fields(db, sid, REQUIRED_FIELD_IDS_EXPECTED)
        == REQUIRED_FIELD_IDS_EXPECTED[3:]
    )

    # All seven filled.
    for i, fid in enumerate(REQUIRED_FIELD_IDS_EXPECTED[3:]):
        make_capture(
            db, sid, source_turn=i + 4,
            keywords=[f"field:{fid}"], statement=f"answer {fid}",
        )
    assert f1_unfilled_required_fields(db, sid, REQUIRED_FIELD_IDS_EXPECTED) == []


def test_required_field_decline(db):
    """An 'I don't know' answer satisfies the field as a preference row."""
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    make_capture(
        db, sid, source_turn=1,
        keywords=["field:concentration_risk"],
        statement="I don't know",
        type_="preference",
    )
    unfilled = f1_unfilled_required_fields(db, sid, REQUIRED_FIELD_IDS_EXPECTED)
    assert "concentration_risk" not in unfilled


def test_session_cannot_complete_without_required_fields(db):
    """A session with status='complete' but missing required fields must still
    report in_progress to the status skill."""
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid, status="complete")
    for i, fid in enumerate(REQUIRED_FIELD_IDS_EXPECTED[:3]):
        make_capture(
            db, sid, source_turn=i + 1,
            keywords=[f"field:{fid}"], statement=f"answer {fid}",
        )
    state, remaining = session_0_status(db)
    assert state == "in_progress"
    assert remaining == 4


def test_two_turn_cap_enforced(db):
    """The required-fields pass must close a field after 2 turns regardless
    of further keyword matches."""
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    fid = "concentration_risk"

    # Turn 1: prompt fires; owner answers with a follow-up keyword present.
    make_capture(
        db, sid, source_turn=1,
        keywords=[f"field:{fid}", "concentration"],
        statement="60 percent one builder",
    )
    assert f4_turns_on_field(db, sid, fid) == 1

    # Turn 2: follow-up fires (turns_on_field < 2 AND keyword matched).
    make_capture(
        db, sid, source_turn=2,
        keywords=[f"field:{fid}", "concentration"],
        statement="years to recover",
    )
    assert f4_turns_on_field(db, sid, fid) == 2

    # Cap check: a third probe would match, but turns_on_field >= 2 must block it.
    cap_blocks_followup = f4_turns_on_field(db, sid, fid) >= 2
    assert cap_blocks_followup is True

    # The field reports as filled to F1.
    unfilled = f1_unfilled_required_fields(db, sid, REQUIRED_FIELD_IDS_EXPECTED)
    assert fid not in unfilled


def test_closing_checkpoint_summary(db):
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    make_capture(db, sid, source_turn=1, keywords=["product"],
                 statement="custom millwork")
    make_capture(
        db, sid, source_turn=2,
        keywords=["field:concentration_risk", "concentration"],
        statement="60 percent one builder",
    )
    rows = f2_checkpoint_summary(db, sid)
    assert len(rows) == 2
    # Discovery row first (source_turn 1, no field tag).
    assert rows[0]["required_field_tag"] is None
    assert rows[0]["statement"] == "custom millwork"
    # Required-field row second (source_turn 2, tagged).
    assert rows[1]["required_field_tag"] == "field:concentration_risk"
    assert rows[1]["statement"] == "60 percent one builder"


def test_owner_correction_at_checkpoint(db):
    """A correction inserts a new row that conflicts_with the prior. History
    is preserved (both rows still queryable)."""
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    prior_id = make_capture(
        db, sid, source_turn=1,
        keywords=["customer-mix"],
        statement="80 percent residential",
    )
    make_capture(
        db, sid, source_turn=2,
        keywords=["customer-mix"],
        statement="60 percent residential, not 80",
        conflicts_with=[prior_id],
    )

    rows = f2_checkpoint_summary(db, sid)
    assert len(rows) == 2  # prior row preserved
    new_row = rows[1]
    new_conflicts = json.loads(new_row["conflicts_with"])
    assert prior_id in new_conflicts


def test_yaml_render_at_close(db):
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)
    for i, fid in enumerate(REQUIRED_FIELD_IDS_EXPECTED):
        make_capture(
            db, sid, source_turn=i + 1,
            keywords=[f"field:{fid}"],
            statement=f"answer for {fid}",
        )
    make_capture(db, sid, source_turn=99, keywords=["product"],
                 statement="custom millwork")

    rendered = f3_render_foundation_yaml(db, sid)
    assert rendered.startswith("# 00-industry.yaml.")

    payload = yaml.safe_load(rendered)
    assert "last_updated" in payload
    assert "required_fields" in payload
    assert "discovery" in payload
    assert "voice_samples" in payload
    assert set(payload["required_fields"].keys()) == set(REQUIRED_FIELD_IDS_EXPECTED)
    assert "product" in payload["discovery"]
    assert payload["discovery"]["product"][0]["statement"] == "custom millwork"


def test_no_opt_data_writes():
    """The migrated Session 0 skill must contain zero references to /opt/data/."""
    body = SESSION_0_SKILL.read_text(encoding="utf-8")
    assert "/opt/data/" not in body, (
        "Session 0 skill should not reference the legacy /opt/data/ path."
    )


def test_status_skill_reports_in_progress(db):
    sid = "onboarding-00-2026-05-10"
    make_session(db, sid)  # active, no required fields filled
    state, remaining = session_0_status(db)
    assert state == "in_progress"
    assert remaining == 7

    # Fill 4 of 7.
    for i, fid in enumerate(REQUIRED_FIELD_IDS_EXPECTED[:4]):
        make_capture(
            db, sid, source_turn=i + 1,
            keywords=[f"field:{fid}"], statement=f"answer {fid}",
        )
    state, remaining = session_0_status(db)
    assert state == "in_progress"
    assert remaining == 3


def test_probe_template_no_chatbot_patterns(industry_yaml):
    """Static lint: every probe template, fallback, and required_field prompt
    must be free of the listed chatbot filler patterns and must contain no
    em dash characters. The probe_style block is documentation and may quote
    forbidden patterns as anti-examples; it is intentionally excluded."""
    targets = []
    for kw, entries in industry_yaml.get("keywords", {}).items():
        for entry in entries:
            targets.append((f"keywords.{kw}", entry["template"]))
    for i, fb in enumerate(industry_yaml.get("fallbacks", [])):
        targets.append((f"fallbacks[{i}]", fb))
    for rf in industry_yaml.get("required_fields", []):
        targets.append((f"required_fields[{rf['id']}].prompt", rf["prompt"]))

    failures = []
    for label, text in targets:
        for pat in FORBIDDEN_LITERAL:
            if pat in text:
                failures.append((label, pat, text))
        if EM_DASH in text:
            failures.append((label, "em-dash", text))
    assert not failures, f"chatbot pattern violations: {failures}"
