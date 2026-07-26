import pytest

from src.lib import killswitch


def test_enabled_by_default(monkeypatch):
    monkeypatch.delenv("MAXWELL_ENABLED", raising=False)
    assert killswitch.enabled()


def test_disabled(monkeypatch):
    for value in ("false", "False", " FALSE "):
        monkeypatch.setenv("MAXWELL_ENABLED", value)
        assert not killswitch.enabled()
        with pytest.raises(SystemExit) as exc:
            killswitch.require_enabled()
        assert exc.value.code == 0  # silent exit, not a failure


def test_enabled_values(monkeypatch):
    for value in ("true", "1", "yes", "anything"):
        monkeypatch.setenv("MAXWELL_ENABLED", value)
        killswitch.require_enabled()  # no exit
