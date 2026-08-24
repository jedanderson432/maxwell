"""Weekly self-monitoring. Exits non-zero on failure; the workflow turns a
failure into a GitHub Issue (failure-only notifications, per constitution).

Usage: python -m src.lib.health
"""

from __future__ import annotations

import datetime as _dt
import json
import sys

from . import budget, config, corpus, killswitch, state

# A piece that is live on the site but this many days newer than anything we
# have actually distributed means the pipeline has stopped moving. Silence is
# no longer evidence of health: see docs/DECISIONS.md, 2026-08-24.
STALENESS_DAYS = 7
HEARTBEAT_FILE = "health.json"


def _newest_site_date(pieces: list) -> str:
    dates = [str(getattr(p, "date", "") or "")[:10] for p in pieces]
    return max((d for d in dates if len(d) == 10), default="")


def _newest_distributed_date() -> tuple[str, str]:
    """(date, source) for the newest piece we can prove was distributed."""
    hf = state.load("hf.json", default={})
    d = str(hf.get("newest_piece_date") or "")[:10]
    if len(d) == 10:
        return d, "state/hf.json"
    # hf.json predates the staleness rule; fall back to the committed snapshot
    # it was built from so the rule still has something to compare.
    jsonl = config.repo_path("corpus", "corpus.jsonl")
    if jsonl.exists():
        best = ""
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            v = str(json.loads(line).get("date") or "")[:10]
            if len(v) == 10 and v > best:
                best = v
        if best:
            return best, "corpus/corpus.jsonl"
    return "", "none"


def _days_between(newer: str, older: str) -> int:
    fmt = "%Y-%m-%d"
    a = _dt.datetime.strptime(newer, fmt)
    b = _dt.datetime.strptime(older, fmt)
    return (a - b).days


def run() -> int:
    killswitch.require_enabled()
    failures: list[str] = []
    notes: list[str] = []

    # 1. Site reachable and parseable.
    pieces: list = []
    try:
        text = corpus.fetch_llms_full()
        pieces = corpus.parse_llms_full(text)
        if len(pieces) < 800:
            failures.append(f"llms-full.txt parsed to only {len(pieces)} pieces (<800)")
        else:
            notes.append(f"site OK: {len(pieces)} pieces")
    except Exception as exc:
        failures.append(f"corpus fetch/parse failed: {exc}")

    # 1b. Staleness: the live site has moved on but distribution has not.
    # This is the check that would have caught the 2026-08-06 Zenodo wedge on
    # 2026-08-13 instead of letting it run silently for 18 days.
    site_newest = _newest_site_date(pieces) if pieces else ""
    dist_newest, dist_source = _newest_distributed_date()
    try:
        if not site_newest:
            notes.append("staleness: skipped (site not readable this run)")
        elif not dist_newest:
            failures.append(
                "staleness: no distributed corpus date is recorded anywhere "
                "(state/hf.json and corpus/corpus.jsonl both unusable)"
            )
        else:
            lag = _days_between(site_newest, dist_newest)
            if lag > STALENESS_DAYS:
                failures.append(
                    f"STALE PIPELINE: newest piece on jedanderson.org is {site_newest}, "
                    f"newest distributed piece is {dist_newest} ({dist_source}) — "
                    f"{lag} days behind, over the {STALENESS_DAYS}-day limit. "
                    "Ingest or distribution has stopped; check the ingest workflow."
                )
            else:
                notes.append(
                    f"staleness OK: site {site_newest} vs distributed {dist_newest} "
                    f"({lag}d, limit {STALENESS_DAYS}d)"
                )
    except Exception as exc:
        failures.append(f"staleness check failed: {exc}")

    # 2. Committed state is valid JSON and internally consistent.
    try:
        manifest = state.load("corpus_manifest.json", default={})
        n_manifest = len(manifest.get("pieces", {}))
        jsonl = config.repo_path("corpus", "corpus.jsonl")
        if jsonl.exists():
            n_rows = sum(1 for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip())
            if n_manifest and abs(n_rows - n_manifest) > 0:
                failures.append(f"corpus.jsonl rows ({n_rows}) != manifest pieces ({n_manifest})")
            else:
                notes.append(f"state OK: {n_rows} rows")
        elif n_manifest:
            failures.append("manifest has pieces but corpus/corpus.jsonl is missing")
    except Exception as exc:
        failures.append(f"state check failed: {exc}")

    # 3. Budget sane.
    try:
        spent, ceiling = budget.spent_usd(), budget.ceiling_usd()
        if spent > ceiling:
            failures.append(f"budget overrun: spent ${spent:.2f} > ceiling ${ceiling:.2f}")
        else:
            notes.append(f"budget OK: ${spent:.2f}/${ceiling:.2f}")
    except Exception as exc:
        failures.append(f"budget check failed: {exc}")

    # 4. MCP listing (informational — absence before first publish is expected).
    try:
        from ..distribute import mcp_registry

        listed = mcp_registry.run()
        notes.append(f"mcp listed: {listed}")
    except Exception as exc:
        notes.append(f"mcp registry check errored (non-fatal): {exc}")

    # 5. Heartbeat: a dated, committed record that this run actually happened.
    # Without it, "no Issue" is ambiguous between healthy and dead.
    now = _dt.datetime.now(_dt.timezone.utc)
    state.save(HEARTBEAT_FILE, {
        "last_health_run": now.strftime("%Y-%m-%d"),
        "last_health_run_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": not failures,
        "site_newest_piece": site_newest,
        "distributed_newest_piece": dist_newest,
        "distributed_source": dist_source,
        "notes": notes,
        "failures": failures,
    })

    print("HEALTH " + json.dumps({"failures": failures, "notes": notes}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
