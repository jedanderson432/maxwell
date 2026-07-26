"""Load MAXWELL configuration (config/maxwell.json) relative to the repo root."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "maxwell.json"


@lru_cache(maxsize=1)
def load() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)
