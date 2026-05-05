from pathlib import Path


LEGACY_CANONICAL_ROOT = r"C:\Users\OpenC\Documents\AI-Orchestrator"


def normalize_repo_root_paths(value, root: Path):
    roots = {
        str(root),
        root.as_posix(),
        LEGACY_CANONICAL_ROOT,
        LEGACY_CANONICAL_ROOT.replace("\\", "/"),
    }

    if isinstance(value, str):
        normalized = value.replace("\\", "/")
        for root_text in sorted(roots, key=len, reverse=True):
            normalized = normalized.replace(root_text.replace("\\", "/"), "")
        normalized = normalized.replace("<REPO_ROOT>/", "").replace("<REPO_ROOT>", "")
        return normalized.lstrip("/")
    if isinstance(value, list):
        return [normalize_repo_root_paths(item, root) for item in value]
    if isinstance(value, dict):
        return {key: normalize_repo_root_paths(item, root) for key, item in value.items()}
    return value
