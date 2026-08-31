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
- **2026-07-26** HF namespace: initially assumed `jedanderson` was taken by
  an unrelated account and defaulted to `jedanderson432/jedanderson-corpus`.
  CORRECTED same day during credential activation: the supplied HF_TOKEN
  authenticates as user `jedanderson` (it was Jed's own account), so the
  dataset is `jedanderson/corpus` per the autopilot's first-choice name.
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
- **2026-07-26** Activation completed with Jed in-session: all five secrets
  set by Jed via `gh secret set` (values never in chat/files), each verified
  by identity calls in CI. First deposits published: HF `jedanderson/corpus`
  (913 rows, hub round-trip OK), Zenodo sandbox 10.5072/zenodo.573102 then
  production concept DOI 10.5281/zenodo.21609424, Archive.org
  `jedanderson-corpus`. npm `jedanderson-corpus-mcp@1.0.0` published by Jed
  (OTP). `mcpName` line added to site repo `mcp/package.json` with Jed's
  explicit authorization (tooling carve-out; no corpus content touched).
- **2026-07-26** Repo flipped **private → public** on Jed's explicit
  instruction after a clean full-history secret scan (case-sensitive token
  patterns + code-path scan: 0 hits). Supersedes the earlier
  private-by-default decision; staging/ remains empty until Phase 3, revisit
  separation before observer calibration data lands.
- **2026-08-24** **Outage post-mortem: 18 days of failed ingest runs
  (2026-08-06 → 2026-08-24), root cause a transient Zenodo 504.**
  On **2026-08-06** (run 31097853312) `POST
  /deposit/depositions/21625791/actions/newversion` *succeeded*, creating
  draft **21823181**; the immediately following `GET` on that draft returned
  **504 Gateway Time-out** and the script died, leaving the draft open and
  unpublished. From **2026-08-07** onward every run re-called `newversion` on
  21625791 and Zenodo refused with `400 files.enabled: "Please remove all
  files first."` — Zenodo will not open a second draft while one is already
  open on the concept. A one-off network blip became a permanent, daily,
  self-perpetuating failure. `ZenodoClient.request` used a bare
  `requests.Session` with no retry, even though `src/lib/http.py` had
  implemented retry-with-backoff on exactly `(429,500,502,503,504)` since
  day one; the Zenodo client simply never used it.
- **2026-08-24** Diagnosis notes — **three of the four suspected causes were
  false**, and the reported symptom was not the real one. (a) Schedules were
  firing: ingest ran daily 07-27→08-24 with no gap, all three workflows
  `active`, `MAXWELL_ENABLED=true`. (b) The corpus fetch was **not** being
  challenged: `curl` with the exact workflow user agent returned `HTTP 200`,
  `Server: Netlify`, `Content-Type: text/markdown`, real markdown body — the
  site is Netlify-fronted, there is no Cloudflare in the path. **The
  autopilot's raw.githubusercontent.com mirror was therefore NOT switched
  on**: it is a fallback for a challenge that is not happening, and moving to
  it would have swapped a working source for an untested one while leaving
  the actual bug in place. (c) `HF_TOKEN` was valid throughout — HF uploads
  and hub round-trips succeeded on every one of the 18 "failed" runs.
- **2026-08-24** The real reason the pipeline *looked* dark: the
  `Commit state + snapshot` step is the **last** step in ingest.yml and had
  no `if: always()`, so the Zenodo failure aborted the job before it ran.
  Distribution to HF had already happened (the step runs earlier), but the
  *record* of it was discarded every day. `state/*.json` and `corpus/` froze
  at the 2026-08-05 content — newest piece **2026-07-24**, 913 rows — which
  is exactly the evidence that suggested the pipeline was dead. The live HF
  dataset `jedanderson/corpus` was in fact current: 918 pieces, last modified
  2026-08-23, containing `essays/missing-chapter-of-ai-safety` (2026-08-05)
  byte-identical to the live site. Fix: `if: always()` on the commit step, so
  a late-stage failure can never again erase the record of earlier successes.
- **2026-08-24** Monitoring was **not** silent, but it was ambiguous.
  Issue **#1** ("MAXWELL failure: ingest 2026-08-06") was filed on the first
  failure and accumulated 18 comments, one per run — the failure-only
  notification design worked as specified. What it could not do is
  distinguish *healthy* from *dead*, since both produce no new signal. Two
  changes: (1) **heartbeat** — `src/lib/health.py` writes `state/health.json`
  (dated, with `ok`, site/distributed newest dates) and health.yml commits it
  on every run, so a stopped scheduler is visible on the commit graph alone;
  (2) **staleness rule** — health fails, and therefore files an Issue, when
  the newest piece on the live site is more than **7 days** newer than the
  newest distributed piece (`state/hf.json.newest_piece_date`, falling back
  to `corpus/corpus.jsonl` for state written before this rule). Verified
  against the live outage: it reports the site at 2026-08-22 vs distributed
  at 2026-07-24, 29 days behind. It would have fired on 2026-08-13.
  health.yml gains `contents: write` and joins ingest's `maxwell-state`
  concurrency group so the two never race on a push.
- **2026-08-24** Zenodo fix: `new_version_draft` now checks
  `links.latest_draft` and **reuses an open unpublished draft** instead of
  blindly POSTing `newversion` (a draft with `submitted: true` is a published
  version and is ignored). `ZenodoClient.request` gained retry-with-backoff
  on `(429,500,502,503,504)`, 4 attempts, rewinding file handles between
  tries. Together these make the step self-healing: the orphaned draft
  21823181 will be adopted, filled, and published on the next production run,
  with no human intervention and no loss of the concept DOI
  10.5281/zenodo.21609424.
- **2026-08-24** **Placeholder gate — the essay that was already published
  unfinished.** `https://jedanderson.org/essays/missing-chapter-of-ai-safety.md`
  still contains, at the load-bearing centre of the piece, the block
  `> **[CASE PENDING—AUTHOR TO SUPPLY.]**` — roughly five hundred words
  deliberately left uncomposed, awaiting Jed's material. **The gate on this
  run therefore failed and ingest was NOT run.** More seriously: that
  placeholder is *already live in the HF dataset*, byte-identical to the
  site — it went out with the 2026-08-06 upload and has been distributed ever
  since. The gate existed only as a manual instruction, so nothing enforced
  it. Now enforced in code: `src/ingest/run.py` refuses to write
  `corpus.jsonl` if any piece body matches `config.placeholder_markers`
  (`CASE PENDING`, `AUTHOR TO SUPPLY`), naming every offending piece.
  Fail-closed is the right default here because Zenodo DOIs are immutable and
  the HF dataset is trained on — an unfinished piece that escapes cannot be
  recalled — and because a paused pipeline is now loudly visible via the
  heartbeat and staleness rule rather than silent.
- **2026-08-31** **Outage closed. Full window: 2026-08-06 → 2026-08-31, 26
  consecutive failed ingest runs** (last green run 31001831116, 2026-08-05;
  first red 31097853312, 2026-08-06; last red 33316866888, 2026-08-30). The
  2026-08-24 analysis above was correct and is confirmed unchanged against
  the 2026-08-30 log, which still fails with the same single error:
  `RuntimeError: Zenodo POST /deposit/depositions/21625791/actions/newversion
  -> 400: files.enabled "Please remove all files first."` — step 8 of 11,
  every earlier step green. The only annotations on the run are that error
  and an unrelated Node 20 deprecation warning. Of the causes re-checked
  this session: secrets were **not** the problem (HF/sandbox-Zenodo/IA steps
  all authenticated and passed on the failing runs), `MAXWELL_ENABLED` was
  `true` throughout (the job ran; a false kill switch would have skipped it),
  llms-full.txt parses cleanly at **920 pieces** so there is **no parse
  drift**, dependency resolution succeeded, and the budget module is not on
  the ingest path at all.
- **2026-08-31** **Why the outage ran 7 days longer than the post-mortem.**
  The 2026-08-24 fix was correct but was committed to
  `fix/zenodo-draft-wedge-and-staleness-monitoring` and never merged. The
  daily schedule runs on `main`, so runs 2026-08-25 → 2026-08-30 kept failing
  against unfixed code. Recorded because the failure mode is invisible in the
  usual places: the branch was green in review, the repo looked "fixed", and
  nothing compares what is scheduled against what is merged. Merged to `main`
  as part of this change.
- **2026-08-31** **The placeholder gate is now a quarantine, not an abort.**
  As written on 2026-08-24 the gate raised and aborted the whole ingest, and
  `essays/missing-chapter-of-ai-safety` still carries `CASE PENDING` /
  `AUTHOR TO SUPPLY` live. Merging it unchanged would have replaced a Zenodo
  wedge with a placeholder wedge — one unfinished essay blocking 919 finished
  ones — which is the exact failure class this whole post-mortem is about.
  `src/ingest/run.py` now **drops the offending piece from `corpus.jsonl`,
  deletes its snapshot so the unfinished prose is not committed to the public
  repo either, and finishes the run**. The safety property is unchanged and
  in fact strengthened: the placeholder that has been live in the HF dataset
  since 2026-08-06 is *removed* by this run. It stays loud rather than
  silent: the piece is listed in `state/corpus_manifest.json.quarantined`
  with a `first_held` date, and `src/lib/health.py` **fails** — and therefore
  files an Issue — for as long as anything is held. It ships automatically
  on the next ingest once Jed fills the block; no code change needed.
- **2026-08-31** Transient-vs-real failure handling unified. `src/lib/http.py`
  now owns `TRANSIENT_STATUS = (429,500,502,503,504)` and a `retry_transient()`
  helper; `ZenodoClient.RETRY_STATUS` references it and the HF `upload_folder`
  / `load_dataset` calls are wrapped in it. Rule: a blip is retried four times
  with exponential backoff and only alarms after the retries are exhausted; a
  400/401/403/404 re-raises on the **first** attempt so a bad token or a
  validation error is never masked by three minutes of sleeping. Archive.org
  already had `retries=5`, and the corpus fetch path already used
  `http.get`'s retry — Zenodo and HF were the two gaps.
- **2026-08-31** Backfill: 7 pieces published or first seen during the outage
  had never been ingested (`nature-aligned-ai` 08-04,
  `missing-chapter-of-ai-safety` 08-05, `why-build-environmental-superintelligence`
  08-18, `environmental-loop-through-time` and
  `who-closes-the-environmental-protection-loop` 08-22, `invention-of-elsewhere`
  08-26, `law-of-larger-selves` 08-27) plus 1 changed piece
  (`why-von-neumann-was-right`). All are picked up by the ordinary incremental
  ingest in the same run that restores the pipeline — no separate backfill
  path — taking the distributed corpus from 913 to **919** rows (920 live
  minus the 1 quarantined piece).
- **2026-08-31** **Zenodo API corrections found while verifying the fix.** Two
  documented behaviours are wrong in production, and each cost one red run:
  (1) `links.latest_draft` **is** present on published deposition 21625791 and
  **does** point at a draft, but the object it returns reports
  `submitted: true` — so the documented "is there an open draft?" check
  answers *no* while draft 21823181 is demonstrably open. The reliable lookup
  is `GET /deposit/depositions?all_versions=true` filtered to
  `submitted == false` and matched on `conceptrecid` (run 33393568266).
  (2) That listing returns **summary** objects whose `links` omit `bucket`, so
  uploading straight from a listing hit raises `KeyError: 'bucket'`; the
  adopted draft must be re-`GET` by id for the full representation
  (run 33393809632). Both are now covered by tests in
  `tests/test_distribute.py` so the next refactor cannot silently undo them.
- **2026-08-31** **Restored.** Run 33393950925 green end to end. The orphaned
  draft 21823181 was adopted, filled and published as
  **10.5281/zenodo.21823181** under the unchanged concept DOI
  **10.5281/zenodo.21609424** (version 2026.08.31, public record round-trip
  OK, 7,309,381-byte archive). Verified from outside the build: HF
  `jedanderson/corpus` at revision `b5cd9f40`, `lastModified`
  2026-08-31T12:48:36Z, **919 rows** via datasets-server, 919 `raw/*.md` and
  no `missing-chapter-of-ai-safety` file — i.e. the placeholder that had been
  live in the dataset since 2026-08-06 is now **removed**. Archive.org item
  `jedanderson-corpus` updated (sha 48a68342ba1f). `state/{zenodo,hf,ia}.json`
  and `state/corpus_manifest.json` all rewritten by the run and committed as
  `ingest: corpus sync 2026-08-31`.
