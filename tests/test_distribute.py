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


def test_newest_piece_date():
    rows = [
        {"date": "2026-01-01"}, {"date": "2026-08-05"}, {"date": "2025-12-31"},
    ]
    assert hf_dataset.newest_piece_date(rows) == "2026-08-05"
    assert hf_dataset.newest_piece_date([{"date": None}]) == ""
    assert hf_dataset.newest_piece_date([]) == ""


class _FakeZenodo(zenodo_deposit.ZenodoClient):
    """ZenodoClient with the network replaced, to exercise draft recovery."""

    def __init__(self, deposition):
        self.env = "production"
        self.base = "https://zenodo.org"
        self._deposition = deposition
        self.newversion_calls = 0

    def get_deposition(self, dep_id):
        return self._deposition

    def request(self, method, url, **kw):  # pragma: no cover - guard
        raise AssertionError(f"unexpected network call: {method} {url}")


def test_new_version_draft_reuses_open_draft(monkeypatch):
    """The 2026-08-06 wedge: an orphaned draft must be reused, not re-created.

    Zenodo answers 400 files.enabled 'Please remove all files first.' to a
    second newversion while a draft is open, which pinned production for 18
    days. Recovery must not require a human.
    """
    draft = {"id": 21823181, "submitted": False}
    client = _FakeZenodo({"links": {"latest_draft": "https://zenodo.org/api/deposit/depositions/21823181"}})
    monkeypatch.setattr(_FakeZenodo, "request", lambda self, m, u, **k: _Resp(draft))
    got = client.new_version_draft(21625791)
    assert got["id"] == 21823181


def test_new_version_draft_creates_when_no_draft_open(monkeypatch):
    client = _FakeZenodo({"links": {}})  # no latest_draft -> must POST newversion
    calls = []

    def fake_request(self, method, url, **kw):
        calls.append((method, url))
        if url.endswith("/actions/newversion"):
            return _Resp({"links": {"latest_draft": "https://zenodo.org/api/deposit/depositions/999"}})
        return _Resp({"id": 999, "submitted": False})

    monkeypatch.setattr(_FakeZenodo, "request", fake_request)
    got = client.new_version_draft(21625791)
    assert got["id"] == 999
    assert any(u.endswith("/actions/newversion") for _, u in calls)


def test_new_version_draft_ignores_published_draft(monkeypatch):
    """A submitted 'draft' is a published version, not a recoverable draft."""
    client = _FakeZenodo({"links": {"latest_draft": "https://zenodo.org/api/deposit/depositions/5"}})
    calls = []

    def fake_request(self, method, url, **kw):
        calls.append((method, url))
        if url.endswith("/actions/newversion"):
            return _Resp({"links": {"latest_draft": "https://zenodo.org/api/deposit/depositions/6"}})
        if url.endswith("/depositions/5"):
            return _Resp({"id": 5, "submitted": True})
        return _Resp({"id": 6, "submitted": False})

    monkeypatch.setattr(_FakeZenodo, "request", fake_request)
    got = client.new_version_draft(4)
    assert got["id"] == 6


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload
