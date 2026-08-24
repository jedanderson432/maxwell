"""INGEST: snapshot the corpus from the live site into corpus/ (idempotent).

- Detects changed content by per-piece hash of the llms-full.txt block.
- Fetches per-piece markdown only for new/changed pieces (rate-limited).
- Never alters original prose: the snapshot is a byte-faithful cache.
- Writes corpus/corpus.jsonl (one JSON object per piece, full metadata)
  and state/corpus_manifest.json (committed memory).

Usage: python -m src.ingest.run [--limit N] [--force]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from ..lib import config, corpus, killswitch, state

MANIFEST = "corpus_manifest.json"


def placeholder_hits(rows: list[dict]) -> list[tuple[str, str]]:
    """Pieces whose body still carries an unfilled author placeholder.

    Zenodo DOIs are immutable and the HF dataset is trained on, so an
    unfinished piece that escapes into distribution cannot be recalled.
    Ingest therefore fails closed rather than publishing one. Discovered
    2026-08-24: the CASE PENDING block in essays/missing-chapter-of-ai-safety
    had already reached the HF dataset (docs/DECISIONS.md).
    """
    markers = config.load().get("placeholder_markers") or []
    hits: list[tuple[str, str]] = []
    for r in rows:
        body = r.get("body_markdown") or ""
        for m in markers:
            if m in body:
                hits.append((r["id"], m))
                break
    return hits


def utc_today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def snapshot_path(piece_id: str):
    return config.repo_path("corpus", "pieces", *piece_id.split("/")).with_suffix(".md")


def write_if_changed(path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def build_row(piece: corpus.Piece, md_text: str) -> dict:
    fm, body = corpus.parse_frontmatter(md_text)
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return {
        "id": piece.id,
        "slug": piece.slug,
        "type": piece.type,
        "title": piece.title,
        "subtitle": piece.subtitle or str(fm.get("subtitle") or ""),
        "date": str(fm.get("date") or piece.date),
        "date_modified": str(fm.get("date_modified") or "") or None,
        "tags": [str(t) for t in tags],
        "license": str(fm.get("license") or piece.license),
        "canonical_url": str(fm.get("canonical_url") or piece.url),
        "doi": str(fm.get("doi") or "") or None,
        "ssrn_url": str(fm.get("ssrn_url") or "") or None,
        "abstract": str(fm.get("abstract") or piece.abstract),
        "original_source": str(fm.get("original_source") or "") or None,
        "author": str(fm.get("author") or "Jed Anderson"),
        "body_markdown": body.strip("\n"),
    }


def run(limit: int | None = None, force: bool = False) -> dict:
    killswitch.require_enabled()

    llms_txt = corpus.fetch_llms_txt()
    llms_full = corpus.fetch_llms_full()
    pieces = corpus.parse_llms_full(llms_full)
    if not pieces:
        raise RuntimeError("llms-full.txt parsed to zero pieces; aborting (no state touched)")
    if limit:
        pieces = pieces[:limit]

    manifest = state.load(MANIFEST, default={})
    entries: dict = manifest.get("pieces", {})
    removed: dict = manifest.get("removed", {})
    stats = {"total": len(pieces), "new": 0, "changed": 0, "unchanged": 0,
             "removed": 0, "failed": 0}
    rows: list[dict] = []
    seen: set[str] = set()
    fetched_since_save = 0

    def checkpoint() -> None:
        # Incremental manifest saves so an interrupted first run resumes
        # instead of refetching everything.
        manifest["pieces"] = entries
        manifest["removed"] = removed
        state.save(MANIFEST, manifest)

    for piece in pieces:
        seen.add(piece.id)
        entry = entries.get(piece.id)
        spath = snapshot_path(piece.id)
        needs_fetch = (
            force
            or entry is None
            or entry.get("block_hash") != piece.block_hash
            or not spath.exists()
        )
        if needs_fetch:
            try:
                md_text, source = corpus.fetch_piece_md(piece)
            except RuntimeError as exc:
                print(f"FETCH FAILED {piece.id}: {exc}", file=sys.stderr)
                stats["failed"] += 1
                if entry is not None and spath.exists():
                    # Keep the previous good snapshot.
                    rows.append(build_row(piece, spath.read_text(encoding="utf-8")))
                continue
            write_if_changed(spath, md_text)
            is_new = entry is None
            entries[piece.id] = {
                "block_hash": piece.block_hash,
                "md_sha256": corpus.sha256_text(md_text),
                "source": source,
                "first_seen": (entry or {}).get("first_seen") or utc_today(),
                "last_changed": utc_today(),
            }
            removed.pop(piece.id, None)
            stats["new" if is_new else "changed"] += 1
            rows.append(build_row(piece, md_text))
            fetched_since_save += 1
            if fetched_since_save >= 25:
                checkpoint()
                fetched_since_save = 0
        else:
            stats["unchanged"] += 1
            rows.append(build_row(piece, spath.read_text(encoding="utf-8")))

    # Pieces that disappeared from llms-full.txt (only meaningful on full runs).
    if not limit:
        for pid in sorted(set(entries) - seen):
            removed[pid] = {**entries.pop(pid), "removed_on": utc_today()}
            spath = snapshot_path(pid)
            if spath.exists():
                spath.unlink()
            stats["removed"] += 1

    # Gate: never write a snapshot that carries unfilled author placeholders
    # into corpus.jsonl, which is what HF/Zenodo/archive.org all build from.
    hits = placeholder_hits(rows)
    if hits:
        listed = ", ".join(f"{pid} ({marker!r})" for pid, marker in hits)
        raise RuntimeError(
            f"PLACEHOLDER GATE: {len(hits)} piece(s) still contain author "
            f"placeholders and will not be distributed: {listed}. "
            "corpus.jsonl was left unchanged. Fill in the placeholder on the "
            "live site (or remove the marker from config placeholder_markers) "
            "and re-run."
        )

    rows.sort(key=lambda r: (r["date"], r["id"]), reverse=True)
    corpus_dir = config.repo_path("corpus")
    corpus_dir.mkdir(parents=True, exist_ok=True)
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n"
    write_if_changed(corpus_dir / "corpus.jsonl", jsonl)
    write_if_changed(corpus_dir / "llms.txt", llms_txt)
    write_if_changed(corpus_dir / "llms-full.txt", llms_full)

    manifest["pieces"] = entries
    manifest["removed"] = removed
    manifest["counts"] = {"pieces": len(rows)}
    manifest["last_run"] = utc_today()
    state.save(MANIFEST, manifest)

    print(f"INGEST {json.dumps(stats)}")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only process first N pieces (testing)")
    ap.add_argument("--force", action="store_true", help="refetch everything")
    args = ap.parse_args()
    stats = run(limit=args.limit, force=args.force)
    if stats["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
