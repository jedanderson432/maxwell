# MAXWELL

Autonomous corpus institution for https://jedanderson.org. Governed by
[MAXWELL_CONSTITUTION.md](MAXWELL_CONSTITUTION.md) (wins all conflicts);
built to [MAXWELL_AUTOPILOT.md](MAXWELL_AUTOPILOT.md).

MAXWELL reads the corpus from the live site only and never writes to the
site or its repo (sanctuary clause). It never sends anything to a human.

## Phase 1 (this repo, current)

| Component | Entry point | Schedule |
|---|---|---|
| Corpus snapshot (INGEST) | `python -m src.ingest.run` | daily (`ingest.yml`) |
| Hugging Face dataset | `python -m src.distribute.hf_dataset` | daily, diff-only |
| Zenodo corpus record (one concept DOI) | `python -m src.distribute.zenodo_deposit --env sandbox\|production` | daily, diff-only |
| Archive.org item | `python -m src.distribute.archive_org` | daily, diff-only |
| MCP registry listing check | `python -m src.distribute.mcp_registry` | weekly (`health.yml`) |
| Health checks | `python -m src.lib.health` | weekly (`health.yml`) |

Safety rails: repository variable `MAXWELL_ENABLED` kill switch (all
workflows gate on it), monthly LLM budget ceiling enforced in
`src/lib/budget.py`, committed state under `state/`, failure-only GitHub
Issues.

Setup: `pip install -r requirements.txt`; tests: `python -m pytest`.
Credentials: [docs/CREDENTIALS.md](docs/CREDENTIALS.md). One-time MCP
publication: [docs/RUNBOOK_MCP.md](docs/RUNBOOK_MCP.md). Decision log:
[docs/DECISIONS.md](docs/DECISIONS.md).
