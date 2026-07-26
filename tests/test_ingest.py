from src.ingest.run import build_row, write_if_changed
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
