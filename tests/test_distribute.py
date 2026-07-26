import pytest

from src.distribute import hf_dataset, zenodo_deposit
from src.lib import config, state

ROWS = [
    {
        "id": "essays/a", "slug": "a", "type": "essay", "title": "A",
        "subtitle": "", "date": "2026-01-01", "date_modified": None,
        "tags": ["x"], "license": "CC-BY-4.0",
        "canonical_url": "https://jedanderson.org/essays/a", "doi": None,
        "ssrn_url": None, "abstract": "abs", "original_source": None,
        "author": "Jed Anderson", "body_markdown": "body",
    }
]


def test_dataset_card_contents():
    card = hf_dataset.dataset_card(ROWS)
    # YAML head must pin the parquet config so raw .md is never loaded as data.
    assert 'path: "data/*.parquet"' in card
    assert "license: cc-by-4.0" in card
    # Constitution: label on every generated artifact.
    assert "Generated and maintained by MAXWELL" in card
    assert "Not individually reviewed by Jed Anderson" in card
    # Card requirements from the autopilot spec.
    assert "environmental superintelligence" in card.lower()
    assert "Jed Anderson, jedanderson.org" in card
    assert "@misc" in card  # citation block
    assert "explicitly cleared for AI use" in card


def test_corpus_hash_stable():
    assert hf_dataset.corpus_hash(ROWS) == hf_dataset.corpus_hash([dict(ROWS[0])])
    changed = [dict(ROWS[0], title="B")]
    assert hf_dataset.corpus_hash(changed) != hf_dataset.corpus_hash(ROWS)


def test_zenodo_production_requires_sandbox_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(state, "state_path", lambda name: tmp_path / name)
    monkeypatch.delenv("MAXWELL_ENABLED", raising=False)
    with pytest.raises(SystemExit) as exc:
        zenodo_deposit.run("production")
    assert "sandbox" in str(exc.value).lower()


def test_zenodo_metadata_shape():
    if not config.repo_path("corpus", "corpus.jsonl").exists():
        pytest.skip("corpus not yet ingested")
    meta = zenodo_deposit.metadata("2026.07.26")["metadata"]
    assert meta["upload_type"] == "dataset"
    assert meta["license"] == "cc-by-4.0"
    assert meta["creators"][0]["name"] == "Anderson, Jed"
    assert meta["creators"][0]["orcid"] == "0009-0003-1807-2459"
    assert meta["related_identifiers"] == [
        {"relation": "isDerivedFrom", "identifier": "https://jedanderson.org"}
    ]
    assert "MAXWELL" in meta["description"]


def test_zenodo_archive_deterministic():
    if not config.repo_path("corpus", "corpus.jsonl").exists():
        pytest.skip("corpus not yet ingested")
    _, sha1 = zenodo_deposit.build_archive()
    _, sha2 = zenodo_deposit.build_archive()
    assert sha1 == sha2
