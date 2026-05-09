"""Pipeline 10-stage smoke test — no LLM calls, just import + module shape."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.mark.parametrize("module_name", [
    "orchestrator.pipeline._helpers",
    "orchestrator.pipeline.stage_capture",
    "orchestrator.pipeline.stage_salience",
    "orchestrator.pipeline.stage_classification",
    "orchestrator.pipeline.stage_hard_rule",
    "orchestrator.pipeline.stage_retrieval",
    "orchestrator.pipeline.stage_system1",
    "orchestrator.pipeline.stage_system2",
    "orchestrator.pipeline.stage_audit",
    "orchestrator.pipeline.stage_owner_state",
    "orchestrator.pipeline.stage_action",
    "orchestrator.pipeline.runner",
])
def test_pipeline_module_imports(module_name):
    """Every pipeline module must be importable. Catches syntax errors early."""
    importlib.import_module(module_name)


def test_jaccard_divergence():
    from orchestrator.pipeline.stage_system2 import jaccard, length_ratio
    assert jaccard("hello world", "hello world") == 1.0
    assert jaccard("apple banana", "carrot date") == 0.0
    # Reasonable middle case
    assert 0.0 < jaccard("the quick brown fox", "the brown fox jumped") < 1.0
    assert 0 <= length_ratio("a", "abc") <= 1.0
