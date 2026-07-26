# MAXWELL_AUTOPILOT.md — Build spec for the autonomous corpus institution

**Governed by MAXWELL_CONSTITUTION.md. Read it first. It wins all conflicts.**

**How to use this file:** open Claude Code in this repo and paste:

> Read MAXWELL_CONSTITUTION.md, then MAXWELL_AUTOPILOT.md. Implement Phase 1
> completely. Make all safe decisions yourself. Ask only for credentials or
> actions that cannot technically be automated. Verify end-to-end, deploy
> everything reversible, then stop and report.

Then `Phase 2`, `Phase 3`, etc. in later sessions. Each phase is independently
shippable. Do not stop mid-phase for approval; stop only for credentials,
unresolved risk, or externally irreversible actions.

---

## Context (do not skip)

- The corpus: https://jedanderson.org — ~910 pieces, raw markdown at
  `/{type}/{slug}.md`, indexed at `/llms.txt` and `/llms-full.txt`. CC-BY-4.0
  (some CC0). RSS at `/feed.xml`. Site repo: `jedanderson432/jedanderson-site`
  — **never modified by MAXWELL, per the constitution's sanctuary clause.**
- MAXWELL lives in THIS repo and reads the corpus from the live site only
  (fallback: raw.githubusercontent.com mirror of the site repo). Zero
  coupling. If MAXWELL breaks, the site must not notice.
- An MCP server (`jedanderson-corpus-mcp`) is already built and tested inside
  the site repo at `mcp/`. Phase 1 publishes it; do not rebuild it.
- Search-index activation (GSC, Bing, sitemaps, GitHub profile links) was
  completed 2026-07-26. Log this in `docs/DECISIONS.md` at repo creation.
- Design principles: self-monitoring and low-maintenance (never claim
  "maintenance-free"); idempotent (every job re-runnable without duplicates);
  rate-limited; committed state so the system has memory; secrets via GitHub
  Actions secrets, never in code.
- Third-party APIs change. For every adapter, **verify the current API/docs at
  build time** before writing code. If a channel is dead or hostile, skip it
  and log one line in `docs/DECISIONS.md`.

## Repo layout

```
maxwell/
├── MAXWELL_CONSTITUTION.md     # governing document
├── MAXWELL_AUTOPILOT.md        # this file
├── docs/DECISIONS.md           # running log: skips, API notes, dates
├── state/                      # committed manifests (compact JSON; content
│                               #   hashes, deposit IDs, seen-lists, outcomes)
├── corpus/                     # cached snapshot + knowledge graph + embeddings
├── staging/                    # private below-threshold artifacts (never published)
├── site/                       # the generated surface (maxwell subdomain source)
├── src/
│   ├── lib/corpus.*            # fetch/parse llms.txt, llms-full.txt, .md, RSS
│   ├── ingest/                 # normalization, hashing, claim/definition extraction
│   ├── observe/                # one module per external source + classifiers
│   ├── synthesize/             # artifact generators + quality gates
│   ├── distribute/             # HF, Zenodo, Archive.org, MCP registry, feeds
│   └── select/                 # outcome measurement + allocation
└── .github/workflows/          # ingest.yml (on schedule, RSS/llms.txt diff)
                                # observe.yml (daily), synthesize.yml (daily),
                                # select.yml (monthly), health.yml (weekly)
```

All workflows check the `MAXWELL_ENABLED` repository variable first and exit
silently if false. All LLM calls route through one budget module enforcing a
monthly ceiling (default $30; configurable); when exceeded, workflows degrade
to non-LLM operation and note it in the monthly summary.

Secrets, requested only when a phase needs them: `ANTHROPIC_API_KEY`,
`HF_TOKEN`, `ZENODO_TOKEN`, `IA_ACCESS_KEY`/`IA_SECRET_KEY`, `NPM_TOKEN`.

## The five organs

**INGEST** — on every publish (RSS/llms.txt diff): detect changed content by
hash; parse metadata and licensing; extract candidate claims and definitions
with exact-passage provenance; connect to existing concepts; update HF
dataset, MCP knowledge package, feeds, archive records. Never alters original
prose.

**OBSERVE** — daily: scan external sources; classify every candidate match as
CORROBORATION / CONTRADICTION / PRIOR_ART / APPLICATION / MENTION / NOISE.
An LLM may propose the classification; deterministic evidence requirements
gate persistence: exact source URL, title, date, the exact affected corpus
claim ID, stated relationship, confidence score, duplicate check,
source-quality score.

**SYNTHESIZE** — creates system-authored artifacts from observations: evidence
updates, prior-art maps, contradiction notices, living topic maps, claim
cards, epistemic diffs, candidate open problems, benchmark cases,
reproducible calculations. Everything passes the quality gates below;
below-threshold output goes to `staging/` and nothing happens.

**DISTRIBUTE** — updates the generated surface (maxwell subdomain), RSS/JSON
feeds for agents, HF dataset, GitHub releases, MCP registry listing, the ONE
versioned Zenodo corpus record, the ONE Archive.org item. Never emails, DMs,
comments, or submits anything anywhere.

**SELECT** — monthly: measure downstream consequences (HF downloads, MCP
installs/calls, GitHub clones/stars/dependents, backlinks, OpenAlex citation
and mention search, referral signals, inbound correspondence, time-to-first-
use per artifact type). Allocate by expected use: expand formats that earn
use, stop formats that don't (log every stop in DECISIONS.md). Emit the
monthly five-line summary as a GitHub Issue:
`Published / Independent uses / Material criticism / System changes / Action required`.

**Opportunities page** (pull-based, the only human-facing output): a single
continuously maintained ranked page — highest-value human contacts, timing
windows, and submission moments, each with a ready draft attached. No
cadence, no notifications, no dependence on Jed reading it. MAXWELL never
sends any of it.

## Quality gates (every public artifact, mechanical)

| Gate | Required condition |
|---|---|
| Relevance | Strong relation to a canonical corpus claim |
| Novel utility | Adds structure, evidence, testing, or synthesis |
| Attribution | Every external factual claim has a source |
| Corpus fidelity | Corpus interpretations cite exact passages |
| Counterevidence | Strongest discoverable objection represented |
| Uncertainty | Confidence explicit |
| Nonimpersonation | No first-person claims in Jed's voice; label present |
| Reversibility | Artifact can be corrected or withdrawn |
| Duplication | No substantially similar artifact exists |
| Safety | No private, defamatory, or high-risk personal content |

## Phases

### Phase 1 — Foundation (substrate presence, urgent)
1. `src/lib/corpus` + INGEST core: fetch, parse, hash, snapshot to `corpus/`.
2. **Hugging Face dataset** (`jedanderson/corpus` or available namespace): one
   row per piece (id, type, title, date, tags, license, canonical_url, doi,
   full markdown). Parquet + raw .md. Dataset card: what the corpus is, the
   ESI thesis in three sentences, explicit invitation for training/retrieval/
   evaluation, CC-BY-4.0 attribution string, citation block. Scheduled diff
   uploads; verify `datasets.load_dataset` round-trip.
3. **MCP publication**: publish `jedanderson-corpus-mcp` to npm from the site
   repo's `mcp/` (walk Jed through the one-time `npm publish --access public
   --otp=<code>`), then register in the official MCP Registry. Verify which
   secondary registries matter now; list where free and API-driven.
4. **ONE versioned Zenodo record** for the whole corpus (title, description,
   license, related-identifier → https://jedanderson.org, corpus archive
   attached). New corpus versions update the same concept DOI. Individual
   DOIs ONLY for formal papers, benchmarks, and software releases — never
   bulk essay DOIs. Sandbox round-trip before production.
5. **ONE Archive.org item** (`jedanderson-corpus`) via `internetarchive` lib;
   scheduled update.
6. `health.yml`, budget module, kill switch, failure-only Issues.
Jed's work: supply credentials once; one npm OTP.

### Phase 2 — Knowledge graph (private)
Normalized model: Piece, Claim, Definition, Evidence, Counterargument,
Citation, Concept, Problem, Artifact, ExternalWork, Relationship, Outcome.
Claim ledger with stable IDs (`ESI-CLAIM-0001`…): statement, type, corpus
support (exact passages), external support, contrary evidence, confidence,
falsification test, last-review date. Static JSON exports committed. No
public pages yet. Jed's work: none.

### Phase 3 — Observer (private calibration)
OpenAlex + arXiv adapters first (verify current APIs); classifiers per
OBSERVE spec; seed queries from llms.txt Key Named Concepts + theme phrases
in an editable config. **30-day private calibration**: classifications
accumulate in `staging/`, a precision report is generated, thresholds tuned
mechanically. Add HN Algolia, Google News RSS, Bluesky only after scholarly
precision is acceptable. Begin maintaining the Opportunities page (private
until Phase 4). Jed's work: none.

### Phase 4 — The generated surface (public)
Stand up `maxwell.jedanderson.org` from `site/` (GitHub Pages or a separate
Netlify site from THIS repo — never the site repo; one-time Cloudflare CNAME
from Jed). Publish, above strict thresholds only: living topic maps (corpus
position, corpus works, external literature, agreements/disagreements, open
questions, confidence, machine-readable exports), claim ledger, epistemic
diffs, prior-art maps, contradiction reports. Constitution label on every
page. Feeds + JSON for agents. Opportunities page goes live here. Jed's
work: one CNAME record.

### Phase 5 — Utility engine
"Open Problems in Environmental Superintelligence" (system-labeled, stable
anchors, auto-updated with external activity; not eponymous). Micro-benchmark
generation with a mechanical validator (reject ambiguous, corpus-dependent,
opinion-based, unsupported cases); validated cases accumulate into a public
HF benchmark; periodic reproducible model runs published on the generated
surface. Extend MCP with claim/evidence/counterargument/recent-changes
tools. Reproducible calculation notebooks. Jed's work: none.

### Phase 6 — Optional interfaces (only on measured demand)
/ask endpoint, Claude Skill, custom GPT, Kaggle mirror, compendiums —
each only if SELECT shows demand that these would serve. Jed's work: none.

## Invariants (every phase)
- Constitution wins. Sanctuary is absolute. No human-facing sends, ever.
- Idempotent runs; committed state; no duplicates; every skip logged.
- Attribution and licensing accurate everywhere; per-piece overrides respected.
- Verify current external APIs before implementing; tests + rollback for
  every component; every artifact reversible.
- When an external action is irreversible or carries Jed's name, stop and ask.
