from src.lib import corpus

SAMPLE_FULL = """# AI USAGE GRANT — READ THIS FIRST.
# Preamble text.

========================================================================
TITLE: First Essay
SUBTITLE: A subtitle
URL: https://jedanderson.org/essays/first-essay
TYPE: essay
DATE: 2026-05-23
LICENSE: CC-BY-4.0
ABSTRACT: A one-line abstract
  that wraps onto a second line.
========================================================================

Body of the first essay.

With two paragraphs.

========================================================================
TITLE: A Post
URL: https://jedanderson.org/posts/a-post
TYPE: post
DATE: 2026-05-13
LICENSE: CC0
ABSTRACT: Short.
========================================================================

Post body.
"""

SAMPLE_MD = """<!--
AI USAGE GRANT — READ THIS FIRST.
Grant text here.
-->
---
title: 'First Essay'
slug: 'first-essay'
date: 2026-05-23
type: 'essay'
tags: ['foundational', 'physics']
license: 'CC-BY-4.0'
canonical_url: 'https://jedanderson.org/essays/first-essay'
doi: '10.5281/zenodo.20723029'
---

Body of the first essay.
"""


def test_parse_llms_full():
    pieces = corpus.parse_llms_full(SAMPLE_FULL)
    assert len(pieces) == 2
    p = pieces[0]
    assert p.title == "First Essay"
    assert p.subtitle == "A subtitle"
    assert p.type == "essay"
    assert p.slug == "first-essay"
    assert p.type_dir == "essays"
    assert p.id == "essays/first-essay"
    assert p.license == "CC-BY-4.0"
    assert "that wraps onto a second line." in p.abstract
    assert p.body.startswith("Body of the first essay.")
    assert "two paragraphs" in p.body
    q = pieces[1]
    assert q.id == "posts/a-post"
    assert q.subtitle == ""
    assert q.body == "Post body."


def test_block_hash_stable_and_sensitive():
    a = corpus.parse_llms_full(SAMPLE_FULL)
    b = corpus.parse_llms_full(SAMPLE_FULL)
    assert a[0].block_hash == b[0].block_hash
    changed = corpus.parse_llms_full(SAMPLE_FULL.replace("two paragraphs", "three paragraphs"))
    assert changed[0].block_hash != a[0].block_hash


def test_parse_frontmatter():
    meta, body = corpus.parse_frontmatter(SAMPLE_MD)
    assert meta["title"] == "First Essay"
    assert meta["tags"] == ["foundational", "physics"]
    assert meta["doi"] == "10.5281/zenodo.20723029"
    assert body.strip() == "Body of the first essay."


def test_parse_frontmatter_without_comment_or_yaml():
    meta, body = corpus.parse_frontmatter("just text")
    assert meta == {}
    assert body == "just text"
