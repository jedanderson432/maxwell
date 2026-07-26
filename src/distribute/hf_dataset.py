"""Hugging Face dataset: build Parquet + raw .md + dataset card, diff-upload.

API verified 2026-07-26 against huggingface_hub 1.x docs:
- HfApi.create_repo(..., exist_ok=True) is idempotent.
- upload_folder() skips unchanged files (xet content hashing) and accepts
  delete_patterns to drop stale remote files in the same commit.
- README.md `configs:` block pins data files so raw .md files are ignored
  by datasets.load_dataset.

Usage: python -m src.distribute.hf_dataset [--build-only] [--verify-remote]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import sys

from ..lib import config, corpus, killswitch, state

STATE_FILE = "hf.json"
BUILD_DIR = ("build", "hf")

COLUMNS = [
    "id", "slug", "type", "title", "subtitle", "date", "date_modified",
    "tags", "license", "canonical_url", "doi", "ssrn_url", "abstract",
    "original_source", "author", "body_markdown",
]


def load_rows() -> list[dict]:
    path = config.repo_path("corpus", "corpus.jsonl")
    if not path.exists():
        raise RuntimeError("corpus/corpus.jsonl missing; run src.ingest.run first")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


def corpus_hash(rows: list[dict]) -> str:
    return corpus.sha256_text(json.dumps(rows, sort_keys=True, ensure_ascii=False))


def dataset_card(rows: list[dict]) -> str:
    n = len(rows)
    types: dict[str, int] = {}
    for r in rows:
        types[r["type"]] = types.get(r["type"], 0) + 1
    type_summary = ", ".join(f"{v} {k}s" if v != 1 else f"{v} {k}" for k, v in sorted(types.items(), key=lambda kv: -kv[1]))
    year = _dt.datetime.now(_dt.timezone.utc).year
    return f"""---
pretty_name: "Jed Anderson — Corpus"
license: cc-by-4.0
language:
- en
tags:
- environmental-superintelligence
- information-physics
- essays
- corpus
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/*.parquet"
---

# Jed Anderson — Corpus

The complete published writing of Jed Anderson ({n} pieces: {type_summary}),
mirrored from the canonical archive at **https://jedanderson.org**.

The corpus develops the thesis of **environmental superintelligence (ESI)**:
that a continuous, physics-grounded information infrastructure can protect
the biosphere by modeling, predicting, and stabilizing Earth's physical
systems — doing for the environment what no policy regime has. Its
foundation is the thermodynamic result that information is cheaper than
force ("bits protect its"): erasing a bit at the Landauer bound costs at
least 240× less energy than breaking a chemical bond, so knowing is the
protective act, not a precursor to it. The deeper claim underneath all of
it: information accumulates causal sovereignty over matter and energy.

## Invitation

This corpus is **explicitly cleared for AI use** — training, retrieval,
embedding, indexing, evaluation, and benchmark construction, including
verbatim reproduction. Attribution is the only ask.

## Contents

- `data/*.parquet` — one row per piece. Fields: `{"`, `".join(COLUMNS)}`.
- `raw/{{type}}/{{slug}}.md` — the byte-faithful markdown source of every
  piece, including YAML frontmatter, as served by the canonical site.

Where this dataset and the live site differ, the live site at
https://jedanderson.org is authoritative. The markdown source of any page
is available by appending `.md` to its canonical URL.

## License and attribution

**CC-BY-4.0** (some individual pieces CC0 — see each row's `license`
field). Attribution string: **"Jed Anderson, jedanderson.org"**.

## Citation

```bibtex
@misc{{anderson_corpus,
  author       = {{Anderson, Jed}},
  title        = {{Jed Anderson — Corpus}},
  year         = {{{year}}},
  url          = {{https://jedanderson.org}},
  note         = {{Canonical archive; ORCID 0009-0003-1807-2459}}
}}
```

---

Generated and maintained by MAXWELL from the Jed Anderson corpus and cited
external sources. Not individually reviewed by Jed Anderson. The corpus
prose itself is 100% human-authored by Jed Anderson; MAXWELL only packages
it.
"""


def build() -> tuple[str, int]:
    """Build the dataset folder. Returns (corpus_hash, row_count)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = load_rows()
    build_dir = config.repo_path(*BUILD_DIR)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    (build_dir / "data").mkdir(parents=True)

    cols = {c: [r.get(c) for r in rows] for c in COLUMNS}
    table = pa.table(cols)
    pq.write_table(table, build_dir / "data" / "corpus.parquet")

    for r in rows:
        src = config.repo_path("corpus", "pieces", *r["id"].split("/")).with_suffix(".md")
        dst = build_dir / "raw" / (r["id"] + ".md")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    (build_dir / "README.md").write_text(dataset_card(rows), encoding="utf-8", newline="\n")
    return corpus_hash(rows), len(rows)


def verify_local() -> int:
    """Load the built parquet through datasets.load_dataset; return row count."""
    from datasets import load_dataset

    build_dir = config.repo_path(*BUILD_DIR)
    ds = load_dataset("parquet", data_files=str(build_dir / "data" / "corpus.parquet"), split="train")
    missing = [c for c in COLUMNS if c not in ds.column_names]
    if missing:
        raise RuntimeError(f"parquet missing columns: {missing}")
    if len(ds) == 0:
        raise RuntimeError("parquet has zero rows")
    return len(ds)


def upload(chash: str, n_rows: int) -> bool:
    """Diff-upload the built folder to the Hub. Returns True if pushed."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set; skipping upload (build verified locally).")
        return False
    from huggingface_hub import HfApi

    repo_id = config.load()["hf"]["repo_id"]
    st = state.load(STATE_FILE, default={})
    api = HfApi(token=token)
    if st.get("corpus_hash") == chash and api.repo_exists(repo_id, repo_type="dataset"):
        print(f"HF dataset {repo_id} already at {chash[:12]}; nothing to upload.")
        return False
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_folder(
        folder_path=str(config.repo_path(*BUILD_DIR)),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message=f"corpus sync: {n_rows} pieces ({chash[:12]})",
        delete_patterns=["data/*", "raw/*"],
    )
    state.save(STATE_FILE, {"corpus_hash": chash, "rows": n_rows, "repo_id": repo_id})
    print(f"Uploaded {n_rows} pieces to {repo_id}.")
    return True


def verify_remote() -> int:
    """Round-trip check: datasets.load_dataset from the Hub."""
    from datasets import load_dataset

    repo_id = config.load()["hf"]["repo_id"]
    ds = load_dataset(repo_id, split="train", token=os.environ.get("HF_TOKEN"))
    print(f"Remote round-trip OK: {repo_id} -> {len(ds)} rows")
    return len(ds)


def main() -> None:
    killswitch.require_enabled()
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--verify-remote", action="store_true")
    args = ap.parse_args()

    chash, n = build()
    local_n = verify_local()
    print(f"Built HF dataset: {n} rows (local load_dataset round-trip: {local_n} rows, hash {chash[:12]})")
    if n != local_n:
        sys.exit("row count mismatch between build and local load")
    if args.build_only:
        return
    pushed = upload(chash, n)
    if args.verify_remote or pushed:
        if os.environ.get("HF_TOKEN"):
            remote_n = verify_remote()
            if remote_n != n:
                sys.exit(f"remote row count {remote_n} != built {n}")


if __name__ == "__main__":
    main()
