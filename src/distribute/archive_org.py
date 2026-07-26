"""Archive.org: ONE item (jedanderson-corpus), scheduled idempotent update.

API verified 2026-07-26 against archive.org/developers (internetarchive
5.x): upload(..., checksum=True) skips files whose MD5 already matches the
item (idempotent); metadata updates go through modify_metadata, not upload.
The library honors env vars IA_ACCESS_KEY_ID / IA_SECRET_ACCESS_KEY (note:
NOT the IA_ACCESS_KEY/IA_SECRET_KEY names in older notes — this module
accepts either and maps them). Keys: https://archive.org/account/s3.php

Usage: python -m src.distribute.archive_org
"""

from __future__ import annotations

import datetime as _dt
import os
import sys

from ..lib import config, killswitch, state
from .zenodo_deposit import build_archive

STATE_FILE = "ia.json"

METADATA = {
    "title": "Jed Anderson — Corpus (complete archive of jedanderson.org)",
    "mediatype": "texts",
    "collection": "opensource",
    "creator": "Jed Anderson",
    "description": (
        "The complete published writing of Jed Anderson — essays, papers, "
        "speeches, and posts on environmental superintelligence, information "
        "physics, and the causal sovereignty of information over matter and "
        "energy. Canonical archive: https://jedanderson.org. Contains the "
        "markdown source of every piece plus a machine-readable corpus.jsonl. "
        "CC-BY-4.0 (some pieces CC0); explicitly cleared for AI training, "
        "retrieval, and evaluation. Attribution: Jed Anderson, jedanderson.org. "
        "Generated and maintained by MAXWELL from the Jed Anderson corpus and "
        "cited external sources. Not individually reviewed by Jed Anderson."
    ),
    "subject": [
        "environmental superintelligence",
        "information physics",
        "corpus",
        "essays",
    ],
    "licenseurl": "https://creativecommons.org/licenses/by/4.0/",
}


def _credentials() -> tuple[str, str] | None:
    access = os.environ.get("IA_ACCESS_KEY_ID") or os.environ.get("IA_ACCESS_KEY")
    secret = os.environ.get("IA_SECRET_ACCESS_KEY") or os.environ.get("IA_SECRET_KEY")
    if access and secret:
        return access, secret
    return None


def run() -> bool:
    killswitch.require_enabled()
    creds = _credentials()
    if not creds:
        print("IA credentials not set (IA_ACCESS_KEY_ID/IA_SECRET_ACCESS_KEY); skipping.")
        return False

    import internetarchive as ia

    identifier = config.load()["ia"]["identifier"]
    archive_path, sha = build_archive()
    st = state.load(STATE_FILE, default={})
    corpus_jsonl = str(config.repo_path("corpus", "corpus.jsonl"))

    if st.get("archive_sha256") == sha and st.get("uploaded"):
        print(f"[ia] corpus unchanged (sha {sha[:12]}); nothing to upload.")
        return False

    access, secret = creds
    md = dict(METADATA, date=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"))
    responses = ia.upload(
        identifier,
        files={os.path.basename(archive_path): archive_path, "corpus.jsonl": corpus_jsonl},
        metadata=md,
        access_key=access,
        secret_key=secret,
        checksum=True,
        verify=True,
        retries=5,
        retries_sleep=30,
    )
    failed = [r for r in responses if r is not None and r.status_code not in (200, None)]
    if failed:
        for r in failed:
            print(f"[ia] upload failure: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)

    # Keep item-level metadata current on updates (upload only sets it at
    # item creation).
    if st.get("uploaded"):
        item = ia.get_item(identifier, config={"s3": {"access": access, "secret": secret}})
        item.modify_metadata(md, access_key=access, secret_key=secret)

    state.save(STATE_FILE, {"identifier": identifier, "archive_sha256": sha, "uploaded": True})
    print(f"[ia] item {identifier} updated (sha {sha[:12]}).")
    return True


if __name__ == "__main__":
    run()
