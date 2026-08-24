"""Staleness rule and heartbeat: silence must not mean both healthy and dead."""

import json

from src.lib import health


def test_days_between():
    assert health._days_between("2026-08-24", "2026-08-05") == 19
    assert health._days_between("2026-08-05", "2026-08-05") == 0


def test_newest_site_date_from_pieces():
    class P:
        def __init__(self, date):
            self.date = date

    assert health._newest_site_date([P("2026-01-01"), P("2026-08-22")]) == "2026-08-22"
    assert health._newest_site_date([]) == ""
    assert health._newest_site_date([P("")]) == ""


def test_newest_distributed_prefers_hf_state(monkeypatch):
    monkeypatch.setattr(
        health.state, "load",
        lambda name, default=None: {"newest_piece_date": "2026-08-22"},
    )
    assert health._newest_distributed_date() == ("2026-08-22", "state/hf.json")


def test_newest_distributed_falls_back_to_corpus_jsonl(monkeypatch, tmp_path):
    """hf.json written before the staleness rule has no date field."""
    monkeypatch.setattr(health.state, "load", lambda name, default=None: {})
    jsonl = tmp_path / "corpus.jsonl"
    jsonl.write_text(
        json.dumps({"date": "2026-07-24"}) + "\n" + json.dumps({"date": "2026-07-01"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(health.config, "repo_path", lambda *parts: jsonl)
    assert health._newest_distributed_date() == ("2026-07-24", "corpus/corpus.jsonl")


def test_staleness_threshold_is_seven_days():
    assert health.STALENESS_DAYS == 7
    # The real outage: site at 2026-08-22, distributed at 2026-07-24.
    assert health._days_between("2026-08-22", "2026-07-24") > health.STALENESS_DAYS
