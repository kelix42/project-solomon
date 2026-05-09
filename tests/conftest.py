"""pytest configuration — adds the repo root to sys.path so test modules can import solomon code."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
