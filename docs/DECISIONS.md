# DECISIONS.md — running log

One line (or a short block) per decision, skip, or API note. Newest last.

- **2026-07-26** Repo created. Search-index activation (GSC, Bing, sitemaps,
  GitHub profile links) was completed 2026-07-26, before repo creation
  (logged here per MAXWELL_AUTOPILOT.md).
- **2026-07-26** Repo `jedanderson432/maxwell` created **private**:
  `staging/` must stay non-public (constitution: below-threshold artifacts),
  and private→public is reversible while the reverse leaks. Revisit at
  Phase 4 (the generated surface can deploy from a private repo via
  Netlify, or the repo can be split).
- **2026-07-26** Language: Python 3.11+ (huggingface_hub, datasets,
  internetarchive are Python-native; the MCP server stays Node in the site
  repo and is not rebuilt here).
- **2026-07-26** HF namespace: `jedanderson` on Hugging Face is taken by an
  unrelated account; dataset defaults to `jedanderson432/jedanderson-corpus`
  (matches GitHub). Configurable in `config/maxwell.json` if Jed registers a
  different namespace.
- **2026-07-26** HF API verified against huggingface_hub 1.x docs:
  `Repository` class and `huggingface-cli` are gone; `upload_folder` is
  idempotent (xet hashing) and takes `delete_patterns`; README `configs:`
  block pins `data/*.parquet` so raw `.md` never loads as data.
- **2026-07-26** Zenodo API verified: legacy deposit API
  (`/api/deposit/depositions`) is still the documented path (RDM records
  API exists but is not Zenodo-documented; client kept thin for later
  migration). Bucket API for files (50 GB/file). New versions via
  `actions/newversion`, draft at `links.latest_draft`. Sandbox uses a
  separate account/token; test DOIs under prefix 10.5072. Production
  deposit is code-gated on a verified sandbox round-trip.
- **2026-07-26** Archive.org verified: internetarchive 5.11; env vars are
  `IA_ACCESS_KEY_ID`/`IA_SECRET_ACCESS_KEY` (NOT the `IA_ACCESS_KEY`/
  `IA_SECRET_KEY` names in the autopilot brief — adapter accepts both).
  mediatype `texts`, community collection `opensource` (no approval
  needed), license via `licenseurl`. `checksum=True` makes uploads
  idempotent.
- **2026-07-26** MCP registry verified: official registry still preview but
  API frozen at v0.1 (`registry.modelcontextprotocol.io/v0.1/servers`).
  server.json schema `2025-12-11`, camelCase fields (`registryType`).
  Publishing requires (a) npm package live with top-level `mcpName` field
  matching the registry name, (b) `mcp-publisher login github` (browser
  OAuth). Both require Jed once — see docs/RUNBOOK_MCP.md.
- **2026-07-26** Secondary MCP registries surveyed: **PulseMCP**
  auto-ingests the official registry weekly (nothing to do); **Glama**
  passively crawls public GitHub (nothing to do). Smithery/mcp.so/Docker
  catalog/Cline marketplace all need manual human-account submissions →
  skipped per constitution (no human-facing sends; MAXWELL creates no
  accounts). Logged as: covered by official registry + passive indexers.
- **2026-07-26** Ingest design: `llms-full.txt` is the manifest (1 request,
  per-piece block hashes); per-piece `.md` fetched only for new/changed
  pieces at ≤4 req/s; fallback to raw.githubusercontent.com mirror of the
  site repo. The site's `corpus.jsonl` export is not served on the live
  site (404), so MAXWELL builds its own from the snapshot.
- **2026-07-26** Zenodo/IA archive zip is built with fixed entry timestamps
  so an unchanged corpus produces a byte-identical archive (idempotent
  deposits, hash-compared in state/).
