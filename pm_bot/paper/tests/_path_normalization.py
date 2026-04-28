from pathlib import Path


REPO_ROOT_PLACEHOLDER = "<REPO_ROOT>"
LEGACY_CANONICAL_ROOT = r"C:\Users\OpenC\Documents\AI-Orchestrator"


def normalize_repo_root_paths(value, root: Path):
    roots = {
        str(root),
        root.as_posix(),
        LEGACY_CANONICAL_ROOT,
        LEGACY_CANONICAL_ROOT.replace("\\", "/"),
    }
    roots.discard(REPO_ROOT_PLACEHOLDER)

    if isinstance(value, str):
        normalized = value
        for root_text in sorted(roots, key=len, reverse=True):
            normalized = normalized.replace(root_text, REPO_ROOT_PLACEHOLDER)
        return normalized
    if isinstance(value, list):
        return [normalize_repo_root_paths(item, root) for item in value]
    if isinstance(value, dict):
        return {key: normalize_repo_root_paths(item, root) for key, item in value.items()}
    return value
