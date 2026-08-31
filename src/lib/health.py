"""Weekly self-monitoring, reported as two independent states.

PIPELINE     — is the machinery working? Site reachable, corpus parseable,
               committed state self-consistent, distribution not stale, budget
               within ceiling. Red here means something is broken and MAXWELL
               cannot fix it alone; this is the only state that files an Issue.
CONTENT_HELD — how many finished-except-for-Jed pieces are being withheld, and
               since when. This is not a fault. The pipeline is healthy and
               deliberately waiting on prose; it distributes everything else
               normally. It escalates to an Issue only after a piece has been
               held CONTENT_HELD_ESCALATE_DAYS days, at which point the wait
               has stopped being a wait and become an omission.

Keeping them apart is the point: "waiting on my prose" and "the pipeline is
broken" must be distinguishable without opening a log (docs/DECISIONS.md,
2026-08-31).

Exit codes: 0 healthy, 1 PIPELINE red, 2 CONTENT_HELD escalation only.

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
# A held piece is a normal state until it plainly is not. Thirty days is one
# full monthly-summary cycle: held through a whole cycle without being filled,
# it needs a human rather than another line in a report.
CONTENT_HELD_ESCALATE_DAYS = 30
HEARTBEAT_FILE = "health.json"

EXIT_OK = 0
EXIT_PIPELINE_RED = 1
EXIT_CONTENT_ESCALATED = 2


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


def _days_since(day: str) -> int:
    try:
        return (
            _dt.datetime.now(_dt.timezone.utc).date()
            - _dt.datetime.strptime(day[:10], "%Y-%m-%d").date()
        ).days
    except (ValueError, TypeError):
        return 0


def content_held(quarantined: dict) -> dict:
    """The CONTENT_HELD state: what is withheld, since when, and for how long.

    Pure accounting -- it never decides that anything is broken. `escalated`
    lists only the pieces held long enough that silence is no longer the right
    answer.
    """
    pieces = {}
    for pid, v in (quarantined or {}).items():
        first_held = str((v or {}).get("first_held") or "")[:10]
        pieces[pid] = {
            "marker": (v or {}).get("marker") or "",
            "first_held": first_held,
            "days_held": _days_since(first_held) if first_held else 0,
        }
    escalated = sorted(
        pid for pid, v in pieces.items() if v["days_held"] > CONTENT_HELD_ESCALATE_DAYS
    )
    return {"count": len(pieces), "pieces": pieces, "escalated": escalated}


def content_held_line(content: dict) -> str:
    """The 'Action required' line for the monthly five-line summary.

    The monthly summary (SELECT phase, select.yml) does not exist yet; this is
    the renderer it will call, kept next to the state it formats so the two
    cannot drift.
    """
    if not content["count"]:
        return "Action required: none."
    parts = ", ".join(
        f"{pid} (held {v['days_held']}d)"
        for pid, v in sorted(content["pieces"].items(), key=lambda kv: -kv[1]["days_held"])
    )
    tail = " — ESCALATED" if content["escalated"] else ""
    return (
        f"Action required: {content['count']} piece(s) awaiting your prose: "
        f"{parts}.{tail}"
    )


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
    quarantined: dict = {}
    try:
        manifest = state.load("corpus_manifest.json", default={})
        n_manifest = len(manifest.get("pieces", {}))
        quarantined = manifest.get("quarantined", {}) or {}
        jsonl = config.repo_path("corpus", "corpus.jsonl")
        if jsonl.exists():
            n_rows = sum(1 for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip())
            if n_manifest and n_rows != n_manifest:
                failures.append(f"corpus.jsonl rows ({n_rows}) != manifest pieces ({n_manifest})")
            else:
                notes.append(f"state OK: {n_rows} rows")
        elif n_manifest:
            failures.append("manifest has pieces but corpus/corpus.jsonl is missing")
    except Exception as exc:
        failures.append(f"state check failed: {exc}")

    # 2b. Content hold. NOT a pipeline fault: ingest withholds a piece whose
    # body still carries an author placeholder and distributes everything else
    # (docs/DECISIONS.md, 2026-08-31). Reported as its own state so a wait on
    # Jed's prose is never mistaken for a broken deposit.
    content = content_held(quarantined)
    if content["count"]:
        notes.append(
            f"CONTENT_HELD {content['count']}: "
            + ", ".join(
                f"{pid} ({v['marker']}, held {v['days_held']}d since {v['first_held']})"
                for pid, v in sorted(content["pieces"].items())
            )
        )
    else:
        notes.append("CONTENT_HELD 0: nothing withheld")

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
    pipeline = "red" if failures else "green"
    state.save(HEARTBEAT_FILE, {
        "last_health_run": now.strftime("%Y-%m-%d"),
        "last_health_run_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline": pipeline,
        "pipeline_failures": failures,
        "content_held": content,
        "content_held_summary_line": content_held_line(content),
        # `ok` stays the single boolean older consumers read: healthy means the
        # pipeline is green AND nothing has been held past the escalation line.
        "ok": pipeline == "green" and not content["escalated"],
        "site_newest_piece": site_newest,
        "distributed_newest_piece": dist_newest,
        "distributed_source": dist_source,
        "notes": notes,
    })

    print(f"PIPELINE {pipeline}" + ("" if not failures else ": " + "; ".join(failures)))
    print(f"CONTENT_HELD {content['count']}" + (
        "" if not content["count"] else ": " + ", ".join(
            f"{pid} since {v['first_held']} ({v['days_held']}d)"
            for pid, v in sorted(content["pieces"].items())
        )
    ))
    print("HEALTH " + json.dumps({
        "pipeline": pipeline, "pipeline_failures": failures,
        "content_held": content, "notes": notes,
    }))

    if failures:
        return EXIT_PIPELINE_RED
    if content["escalated"]:
        print(
            "CONTENT_HELD ESCALATED: "
            + ", ".join(
                f"{pid} held {content['pieces'][pid]['days_held']}d "
                f"(> {CONTENT_HELD_ESCALATE_DAYS}d)"
                for pid in content["escalated"]
            )
        )
        return EXIT_CONTENT_ESCALATED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(run())
