from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TMP_PATH_ROOT = REPO_ROOT / "tests" / "__pycache__" / "tmp"
TMP_PATH_ROOT.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def tmp_path() -> Path:
    path = TMP_PATH_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path
