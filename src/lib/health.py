"""Weekly self-monitoring. Exits non-zero on failure; the workflow turns a
failure into a GitHub Issue (failure-only notifications, per constitution).

Usage: python -m src.lib.health
"""

from __future__ import annotations

import json
import sys

from . import budget, config, corpus, killswitch, state


def run() -> int:
    killswitch.require_enabled()
    failures: list[str] = []
    notes: list[str] = []

    # 1. Site reachable and parseable.
    try:
        text = corpus.fetch_llms_full()
        pieces = corpus.parse_llms_full(text)
        if len(pieces) < 800:
            failures.append(f"llms-full.txt parsed to only {len(pieces)} pieces (<800)")
        else:
            notes.append(f"site OK: {len(pieces)} pieces")
    except Exception as exc:
        failures.append(f"corpus fetch/parse failed: {exc}")

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

    print("HEALTH " + json.dumps({"failures": failures, "notes": notes}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
