from src.ingest.run import build_row, placeholder_hits, write_if_changed
from src.lib import corpus

MD = """<!--
grant
-->
---
title: 'T'
slug: 's'
date: 2026-01-02
type: 'essay'
tags: ['a', 'b']
license: 'CC0'
canonical_url: 'https://jedanderson.org/essays/s'
doi: '10.5281/zenodo.1'
date_modified: 2026-01-03
---

Body.
"""


def make_piece() -> corpus.Piece:
    return corpus.Piece(
        title="T", url="https://jedanderson.org/essays/s", type="essay",
        date="2026-01-02", license="CC-BY-4.0", abstract="A", body="Body.",
    )


def test_build_row_prefers_frontmatter():
    row = build_row(make_piece(), MD)
    assert row["id"] == "essays/s"
    assert row["tags"] == ["a", "b"]
    assert row["license"] == "CC0"  # frontmatter override wins
    assert row["doi"] == "10.5281/zenodo.1"
    assert row["date_modified"] == "2026-01-03"
    assert row["body_markdown"] == "Body."


def test_build_row_falls_back_to_block():
    row = build_row(make_piece(), "no frontmatter body")
    assert row["license"] == "CC-BY-4.0"
    assert row["tags"] == []
    assert row["doi"] is None
    assert row["abstract"] == "A"


def test_write_if_changed_idempotent(tmp_path):
    p = tmp_path / "x" / "f.md"
    assert write_if_changed(p, "hello") is True
    assert write_if_changed(p, "hello") is False
    assert write_if_changed(p, "hello2") is True


def test_placeholder_gate_catches_unfilled_block():
    """Unfinished prose must never reach an immutable DOI or a training set."""
    rows = [{
        "id": "essays/x",
        "body_markdown": "Intro.\n\n> **[CASE PENDING—AUTHOR TO SUPPLY.]** ...\n\nOutro.",
    }]
    assert placeholder_hits(rows) == [("essays/x", "CASE PENDING")]


def test_placeholder_gate_passes_finished_prose():
    rows = [{"id": "essays/y", "body_markdown": "A finished essay about a river."}]
    assert placeholder_hits(rows) == []


def test_placeholder_gate_reports_every_offending_piece():
    rows = [
        {"id": "essays/a", "body_markdown": "CASE PENDING here"},
        {"id": "essays/b", "body_markdown": "clean"},
        {"id": "essays/c", "body_markdown": "AUTHOR TO SUPPLY here"},
    ]
    assert [pid for pid, _ in placeholder_hits(rows)] == ["essays/a", "essays/c"]


def test_quarantine_withholds_only_the_offending_piece(monkeypatch, tmp_path):
    """One unfinished essay must not stop the other 919 from distributing.

    Regression guard for the 2026-08-06 outage class: the failure mode being
    prevented is "one stuck item wedges the whole pipeline", so the gate drops
    the piece and lets the run finish rather than aborting it.
    """
    from src.ingest import run as ingest

    piece_ok = corpus.Piece(
        title="OK", url="https://jedanderson.org/essays/ok", type="essay",
        date="2026-08-20", license="CC-BY-4.0", abstract="A", body="Finished.",
    )
    piece_bad = corpus.Piece(
        title="Bad", url="https://jedanderson.org/essays/bad", type="essay",
        date="2026-08-21", license="CC-BY-4.0", abstract="B", body="x",
    )
    monkeypatch.setattr(ingest.corpus, "fetch_llms_txt", lambda: "llms")
    monkeypatch.setattr(ingest.corpus, "fetch_llms_full", lambda: "full")
    monkeypatch.setattr(ingest.corpus, "parse_llms_full", lambda _t: [piece_ok, piece_bad])
    monkeypatch.setattr(
        ingest.corpus, "fetch_piece_md",
        lambda p: (("Finished prose.", "site") if p.slug == "ok"
                   else ("> **[CASE PENDING—AUTHOR TO SUPPLY.]**", "site")),
    )
    monkeypatch.setattr(ingest.config, "repo_path", lambda *parts: tmp_path.joinpath(*parts))
    saved: dict = {}
    monkeypatch.setattr(ingest.state, "load", lambda name, default=None: default or {})
    monkeypatch.setattr(ingest.state, "save", lambda name, data: saved.update({name: data}))
    monkeypatch.setattr(ingest.killswitch, "require_enabled", lambda: None)

    stats = ingest.run()

    assert stats["quarantined"] == 1
    lines = (tmp_path / "corpus" / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "CASE PENDING" not in "\n".join(lines)
    manifest = saved[ingest.MANIFEST]
    assert list(manifest["quarantined"]) == ["essays/bad"]
    # Consistency invariant health.py checks: rows == manifest pieces.
    assert manifest["counts"]["pieces"] == len(manifest["pieces"]) == 1
    # The unfinished prose is not committed to the public repo either.
    assert not (tmp_path / "corpus" / "pieces" / "essays" / "bad.md").exists()
