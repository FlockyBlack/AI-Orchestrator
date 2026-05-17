from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

PMBOT_ARTIFACT_DIR_ENV = "PMBOT_ARTIFACT_DIR"
DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")


def resolve_artifact_root(
    artifact_root: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    if artifact_root:
        return Path(artifact_root)
    source = os.environ if environ is None else environ
    configured = str(source.get(PMBOT_ARTIFACT_DIR_ENV, "") or "").strip()
    if configured:
        return Path(configured)
    return DEFAULT_ARTIFACT_ROOT


def resolve_artifact_subdir(
    dir_name: str,
    *,
    artifact_dir: str | Path | None = None,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    if artifact_dir:
        return Path(artifact_dir)
    return resolve_artifact_root(artifact_root, environ=environ) / dir_name
