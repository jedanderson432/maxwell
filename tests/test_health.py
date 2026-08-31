"""Staleness rule and heartbeat: silence must not mean both healthy and dead."""

import datetime as _dt
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


class _P:
    def __init__(self, date):
        self.date = date


def _green_pipeline(monkeypatch, tmp_path, quarantined):
    """Wire health.run() so PIPELINE is unambiguously green."""
    manifest = {"pieces": {f"p{i}": {} for i in range(900)}, "quarantined": quarantined}
    jsonl = tmp_path / "corpus.jsonl"
    jsonl.write_text(
        "\n".join(json.dumps({"date": "2026-08-27"}) for _ in range(900)) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(health.killswitch, "require_enabled", lambda: None)
    monkeypatch.setattr(health.corpus, "fetch_llms_full", lambda: "x")
    monkeypatch.setattr(health.corpus, "parse_llms_full",
                        lambda _t: [_P("2026-08-27")] * 900)
    monkeypatch.setattr(health.config, "repo_path", lambda *parts: jsonl)
    monkeypatch.setattr(
        health.state, "load",
        lambda name, default=None: (
            manifest if name == "corpus_manifest.json"
            else {"newest_piece_date": "2026-08-27"}
        ),
    )
    written: dict = {}
    monkeypatch.setattr(health.state, "save", lambda name, data: written.update(data))
    monkeypatch.setattr(health.budget, "spent_usd", lambda: 0.0)
    monkeypatch.setattr(health.budget, "ceiling_usd", lambda: 30.0)
    import src.distribute.mcp_registry as mcp
    monkeypatch.setattr(mcp, "run", lambda: True)
    return written


def test_content_held_does_not_turn_pipeline_red(monkeypatch, tmp_path):
    """"Waiting on Jed's prose" must not read as "the pipeline is broken".

    A held piece used to append to `failures`, which turned health red and
    filed an Issue -- indistinguishable from a dead deposit. It is now its own
    state and files nothing.
    """
    written = _green_pipeline(monkeypatch, tmp_path, {
        "essays/missing-chapter-of-ai-safety": {
            "marker": "CASE PENDING", "first_held": "2026-08-31",
        }
    })

    rc = health.run()

    assert rc == health.EXIT_OK, "a content hold must not fail the health run"
    assert written["pipeline"] == "green"
    assert written["pipeline_failures"] == []
    assert written["content_held"]["count"] == 1
    assert written["content_held"]["escalated"] == []
    assert written["ok"] is True


def test_content_held_escalates_after_thirty_days(monkeypatch, tmp_path):
    held_since = (
        _dt.date(2026, 8, 31) - _dt.timedelta(days=health.CONTENT_HELD_ESCALATE_DAYS + 5)
    ).isoformat()
    monkeypatch.setattr(health, "_days_since",
                        lambda day: health.CONTENT_HELD_ESCALATE_DAYS + 5)
    written = _green_pipeline(monkeypatch, tmp_path, {
        "essays/x": {"marker": "CASE PENDING", "first_held": held_since},
    })

    rc = health.run()

    assert rc == health.EXIT_CONTENT_ESCALATED
    assert written["pipeline"] == "green", "escalation is not a pipeline fault"
    assert written["content_held"]["escalated"] == ["essays/x"]
    assert written["ok"] is False


def test_pipeline_red_takes_precedence_over_content_hold(monkeypatch, tmp_path):
    written = _green_pipeline(monkeypatch, tmp_path, {
        "essays/x": {"marker": "CASE PENDING", "first_held": "2026-08-31"},
    })
    monkeypatch.setattr(health.corpus, "parse_llms_full", lambda _t: [])

    assert health.run() == health.EXIT_PIPELINE_RED
    assert written["pipeline"] == "red"


def test_content_held_line_renders_for_the_monthly_summary():
    empty = health.content_held({})
    assert health.content_held_line(empty) == "Action required: none."
    one = health.content_held({"essays/x": {"marker": "CASE PENDING",
                                            "first_held": "2026-08-31"}})
    line = health.content_held_line(one)
    assert "essays/x" in line and "Action required: 1 piece(s)" in line
    assert "ESCALATED" not in line


def test_content_held_counts_days_from_first_held(monkeypatch):
    monkeypatch.setattr(health, "_days_since", lambda day: 12)
    c = health.content_held({"essays/x": {"marker": "AUTHOR TO SUPPLY",
                                          "first_held": "2026-08-19"}})
    assert c["count"] == 1
    assert c["pieces"]["essays/x"]["days_held"] == 12
    assert c["escalated"] == []
