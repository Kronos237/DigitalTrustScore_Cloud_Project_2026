"""Metadata persistence for trained benchmark artifacts."""

import json
from pathlib import Path


def save_metadata(metadata: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))