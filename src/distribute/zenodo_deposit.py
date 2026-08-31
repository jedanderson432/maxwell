"""Zenodo: ONE versioned record for the whole corpus (concept DOI stable).

API verified 2026-07-26 against developers.zenodo.org: the legacy deposit
API (/api/deposit/depositions) remains the documented, supported path; the
bucket API handles file uploads; new versions share the concept DOI via
POST .../actions/newversion (new draft URL in links.latest_draft).

Constitution/autopilot rails enforced here:
- Sandbox round-trip must succeed before production is allowed.
- Individual DOIs are never minted for bulk essays: this module manages
  exactly one corpus record.
- Idempotent: unchanged corpus -> no new version.

Env: ZENODO_SANDBOX_TOKEN, ZENODO_TOKEN (scopes deposit:write + deposit:actions).
Usage: python -m src.distribute.zenodo_deposit --env sandbox|production
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
import zipfile

import requests

from ..lib import config, corpus, http, killswitch, state

STATE_FILE = "zenodo.json"
ARCHIVE_NAME = "jedanderson-corpus.zip"
# Fixed zip entry timestamp so an unchanged corpus produces a byte-identical
# archive (idempotence).
ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def build_archive() -> tuple[str, str]:
    """Zip the corpus snapshot deterministically. Returns (path, sha256)."""
    corpus_dir = config.repo_path("corpus")
    if not (corpus_dir / "corpus.jsonl").exists():
        raise RuntimeError("corpus/corpus.jsonl missing; run src.ingest.run first")
    build_dir = config.repo_path("build", "zenodo")
    build_dir.mkdir(parents=True, exist_ok=True)
    archive = build_dir / ARCHIVE_NAME
    files = sorted(
        p for p in corpus_dir.rglob("*") if p.is_file()
    )
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = "jedanderson-corpus/" + p.relative_to(corpus_dir).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, p.read_bytes())
    import hashlib

    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    return str(archive), sha


def metadata(version: str) -> dict:
    z = config.load()["zenodo"]
    n_pieces = sum(1 for _ in open(config.repo_path("corpus", "corpus.jsonl"), encoding="utf-8"))
    description = (
        f"<p>The complete published writing of Jed Anderson ({n_pieces} pieces) — "
        "essays, papers, speeches, and posts on environmental superintelligence, "
        "information physics, and the causal sovereignty of information over "
        "matter and energy. Canonical archive: "
        '<a href="https://jedanderson.org">https://jedanderson.org</a>. '
        "The archive contains the markdown source of every piece plus a "
        "machine-readable corpus.jsonl (one JSON object per piece with full "
        "metadata).</p>"
        "<p>Content is CC-BY-4.0 (some pieces CC0 — see per-piece metadata) and "
        "explicitly cleared for AI training, retrieval, and evaluation. "
        'Attribution: "Jed Anderson, jedanderson.org".</p>'
        "<p>Generated and maintained by MAXWELL from the Jed Anderson corpus and "
        "cited external sources. Not individually reviewed by Jed Anderson. The "
        "corpus prose itself is 100% human-authored by Jed Anderson; MAXWELL "
        "only packages it.</p>"
    )
    return {
        "metadata": {
            "title": z["title"],
            "upload_type": "dataset",
            "description": description,
            "creators": z["creators"],
            "license": "cc-by-4.0",
            "access_right": "open",
            "version": version,
            "publication_date": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"),
            "keywords": z["keywords"],
            "related_identifiers": [
                {"relation": "isDerivedFrom", "identifier": "https://jedanderson.org"}
            ],
        }
    }


class ZenodoClient:
    def __init__(self, env: str):
        z = config.load()["zenodo"]
        if env == "sandbox":
            self.base = z["sandbox_base"]
            token = os.environ.get("ZENODO_SANDBOX_TOKEN")
        elif env == "production":
            self.base = z["production_base"]
            token = os.environ.get("ZENODO_TOKEN")
        else:
            raise ValueError(env)
        if not token:
            raise SystemExit(
                f"token for {env} not set "
                f"({'ZENODO_SANDBOX_TOKEN' if env == 'sandbox' else 'ZENODO_TOKEN'}); skipping."
            )
        self.env = env
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def _url(self, path: str) -> str:
        return f"{self.base}/api{path}"

    # Transient Zenodo 5xx/429 must not become permanent state damage: a 504
    # between "newversion" and the follow-up GET on 2026-08-06 orphaned a draft
    # and wedged production for 18 days (see docs/DECISIONS.md).
    RETRY_STATUS = http.TRANSIENT_STATUS

    def request(self, method: str, url: str, *, retries: int = 4, **kw) -> requests.Response:
        last = ""
        for attempt in range(retries + 1):
            try:
                resp = self.s.request(method, url, timeout=300, **kw)
            except requests.RequestException as exc:
                last = f"{type(exc).__name__}: {exc}"
            else:
                if resp.status_code < 400:
                    return resp
                last = f"{resp.status_code}: {resp.text[:500]}"
                if resp.status_code not in self.RETRY_STATUS:
                    break
            if attempt < retries:
                # A retried write may have landed server-side; callers that
                # create drafts reconcile via _existing_draft() before retrying.
                time.sleep(2**attempt)
                if hasattr(kw.get("data"), "seek"):
                    kw["data"].seek(0)
        raise RuntimeError(f"Zenodo {method} {url} -> {last}")

    def create_deposition(self) -> dict:
        return self.request("POST", self._url("/deposit/depositions"), json={}).json()

    def get_deposition(self, dep_id) -> dict:
        return self.request("GET", self._url(f"/deposit/depositions/{dep_id}")).json()

    def _existing_draft(self, dep_id) -> dict | None:
        """Return the unpublished new-version draft of dep_id, if one exists.

        Zenodo refuses a second POST .../actions/newversion while an
        unpublished draft is already open on the concept, answering 400
        files.enabled "Please remove all files first." Reusing the open draft
        makes the step idempotent and self-healing after a crash mid-version.
        """
        links = self.get_deposition(dep_id).get("links", {})
        draft_url = links.get("latest_draft")
        if not draft_url:
            return None
        try:
            draft = self.request("GET", draft_url).json()
        except RuntimeError:
            return None
        return None if draft.get("submitted") else draft

    def new_version_draft(self, dep_id) -> dict:
        existing = self._existing_draft(dep_id)
        if existing is not None:
            print(
                f"[{self.env}] reusing open new-version draft {existing['id']} "
                f"(left by an earlier interrupted run)"
            )
            return existing
        resp = self.request(
            "POST", self._url(f"/deposit/depositions/{dep_id}/actions/newversion")
        ).json()
        draft_url = resp["links"]["latest_draft"]
        return self.request("GET", draft_url).json()

    def upload_file(self, dep: dict, path: str) -> None:
        bucket = dep["links"]["bucket"]
        name = os.path.basename(path)
        # Replace the carried-over copy of the same file, if any.
        for f in self.get_deposition(dep["id"]).get("files", []):
            if f["filename"] == name:
                self.request(
                    "DELETE", self._url(f"/deposit/depositions/{dep['id']}/files/{f['id']}")
                )
        with open(path, "rb") as fh:
            self.request("PUT", f"{bucket}/{name}", data=fh)

    def set_metadata(self, dep_id, meta: dict) -> dict:
        return self.request("PUT", self._url(f"/deposit/depositions/{dep_id}"), json=meta).json()

    def publish(self, dep_id) -> dict:
        return self.request(
            "POST", self._url(f"/deposit/depositions/{dep_id}/actions/publish")
        ).json()

    def get_record(self, recid) -> dict:
        return self.request("GET", self._url(f"/records/{recid}")).json()


def run(env: str) -> dict | None:
    killswitch.require_enabled()
    st = state.load(STATE_FILE, default={})

    if env == "production" and not st.get("sandbox", {}).get("verified_roundtrip"):
        raise SystemExit(
            "REFUSING production deposit: sandbox round-trip has not been "
            "verified (state/zenodo.json sandbox.verified_roundtrip is not true). "
            "Run with --env sandbox first."
        )

    archive_path, sha = build_archive()
    env_state = st.get(env, {})
    if env_state.get("archive_sha256") == sha and env_state.get("latest_recid"):
        print(f"[{env}] corpus unchanged (sha {sha[:12]}); no new version needed.")
        return None

    client = ZenodoClient(env)
    version = _dt.datetime.now(_dt.timezone.utc).strftime("%Y.%m.%d")

    if env_state.get("latest_id"):
        dep = client.new_version_draft(env_state["latest_id"])
        print(f"[{env}] created new-version draft {dep['id']}")
    else:
        dep = client.create_deposition()
        print(f"[{env}] created deposition {dep['id']}")

    client.upload_file(dep, archive_path)
    client.set_metadata(dep["id"], metadata(version))
    published = client.publish(dep["id"])

    recid = published.get("record_id") or published.get("id")
    doi = published.get("doi") or published.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    concept_doi = published.get("conceptdoi")
    concept_recid = published.get("conceptrecid")

    # Round-trip: fetch the published record back through the public API.
    record = client.get_record(recid)
    ok = record.get("id") is not None
    print(
        f"[{env}] published: recid={recid} doi={doi} concept_doi={concept_doi} "
        f"round-trip={'OK' if ok else 'FAILED'}"
    )

    st[env] = {
        "latest_id": dep["id"],
        "latest_recid": recid,
        "doi": doi,
        "concept_doi": concept_doi,
        "concept_recid": concept_recid,
        "version": version,
        "archive_sha256": sha,
        "verified_roundtrip": bool(ok),
    }
    state.save(STATE_FILE, st)
    if not ok:
        sys.exit(1)
    return st[env]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", choices=["sandbox", "production"], required=True)
    args = ap.parse_args()
    run(args.env)


if __name__ == "__main__":
    main()
