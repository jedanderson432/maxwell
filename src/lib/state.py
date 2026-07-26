"""Committed state manifests (state/*.json).

Compact JSON, deterministic key order, atomic writes, and no-op writes
skipped so that unchanged runs produce no diff (idempotence).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from . import config


def state_path(name: str) -> Path:
    return config.repo_path("state", name)


def load(name: str, default=None):
    p = state_path(name)
    if not p.exists():
        return {} if default is None else default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(name: str, data) -> bool:
    """Write state atomically. Returns True if the file changed."""
    p = state_path(name)
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if p.exists() and p.read_text(encoding="utf-8") == text:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return True
