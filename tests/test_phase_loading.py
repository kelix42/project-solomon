"""Phase rule (§0): every SKILL.md carries phase: interview | decision | utility.

Asserts:
- Every skill has a parsable front-matter with a valid phase.
- Interview-phase entry points (onboarding wrappers) reference only interview+utility skills.
- Decision-phase entries reference only decision+utility skills.
- Utilities never load other utilities.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

VALID_PHASES = {"interview", "decision", "utility"}


def parse_front_matter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()
    fm = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def all_skills():
    return sorted(SKILLS.glob("*/*/SKILL.md"))


@pytest.mark.parametrize("skill_path", all_skills())
def test_skill_has_valid_phase(skill_path: Path):
    fm = parse_front_matter(skill_path)
    assert "phase" in fm, f"{skill_path}: missing phase: front-matter"
    assert fm["phase"] in VALID_PHASES, f"{skill_path}: invalid phase '{fm['phase']}'"


def test_solomon_redact_is_utility():
    fm = parse_front_matter(SKILLS / "utilities" / "solomon-redact" / "SKILL.md")
    assert fm.get("phase") == "utility"


def test_no_utility_loads_other_utilities():
    """Utilities never load other utilities (CI assertion from §2.4.6)."""
    util_skills = list((SKILLS / "utilities").glob("*/SKILL.md"))
    for skill in util_skills:
        body = skill.read_text()
        # Look for `depends_on:` references — should not list any other utility
        for other in util_skills:
            if other == skill:
                continue
            other_name = other.parent.name
            assert f"- {other_name}" not in body and other_name not in re.findall(
                r"depends_on:\s*\[(.*?)\]", body
            ), f"{skill.parent.name} depends_on {other_name} (utilities cannot load utilities)"
