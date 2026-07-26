"""Verify each configured credential with a real authenticated call.

Prints one line per credential: ABSENT, VALID (with account identity), or
INVALID (with the API status). Never prints secret values. Intended to run
in CI where the secrets live; exits non-zero if any PRESENT credential is
invalid (absent ones are not failures).

Usage: python -m src.lib.verify_credentials
"""

from __future__ import annotations

import os
import sys

import requests

from . import config


def check_hf() -> tuple[str, str]:
    token = os.environ.get("HF_TOKEN")
    if not token:
        return "ABSENT", ""
    from huggingface_hub import HfApi

    try:
        who = HfApi(token=token).whoami()
        return "VALID", f"user={who.get('name')} (type={who.get('type')})"
    except Exception as exc:
        return "INVALID", type(exc).__name__


def _check_zenodo(base: str, env_var: str) -> tuple[str, str]:
    token = os.environ.get(env_var)
    if not token:
        return "ABSENT", ""
    r = requests.get(
        f"{base}/api/deposit/depositions",
        params={"size": 1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    if r.status_code == 200:
        return "VALID", f"depositions endpoint OK ({len(r.json())} visible)"
    return "INVALID", f"HTTP {r.status_code}"


def check_zenodo_sandbox() -> tuple[str, str]:
    return _check_zenodo(config.load()["zenodo"]["sandbox_base"], "ZENODO_SANDBOX_TOKEN")


def check_zenodo_production() -> tuple[str, str]:
    return _check_zenodo(config.load()["zenodo"]["production_base"], "ZENODO_TOKEN")


def check_ia() -> tuple[str, str]:
    access = os.environ.get("IA_ACCESS_KEY_ID") or os.environ.get("IA_ACCESS_KEY")
    secret = os.environ.get("IA_SECRET_ACCESS_KEY") or os.environ.get("IA_SECRET_KEY")
    if not (access and secret):
        return "ABSENT", ""
    try:
        from internetarchive import get_user_info

        info = get_user_info(access, secret)
        ident = info.get("username") or info.get("screenname") or "ok"
        return "VALID", f"account={ident}"
    except Exception as exc:
        return "INVALID", type(exc).__name__


CHECKS = {
    "HF_TOKEN": check_hf,
    "ZENODO_SANDBOX_TOKEN": check_zenodo_sandbox,
    "ZENODO_TOKEN": check_zenodo_production,
    "IA keys": check_ia,
}


def main() -> int:
    bad = 0
    for name, fn in CHECKS.items():
        try:
            status, detail = fn()
        except Exception as exc:  # network etc.
            status, detail = "ERROR", type(exc).__name__
        print(f"CREDENTIAL {name}: {status}" + (f" — {detail}" if detail else ""))
        if status in ("INVALID", "ERROR"):
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
