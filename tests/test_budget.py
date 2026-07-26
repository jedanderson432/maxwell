import datetime as dt

import pytest

from src.lib import budget, state


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "state_path", lambda name: tmp_path / name)


NOW = dt.datetime(2026, 7, 26, tzinfo=dt.timezone.utc)


def test_ceiling_enforced():
    ceiling = budget.ceiling_usd()
    assert ceiling == 30.0
    budget.charge(ceiling - 1.0, now=NOW)
    assert budget.remaining_usd(now=NOW) == pytest.approx(1.0)
    with pytest.raises(budget.BudgetExceeded):
        budget.charge(1.5, now=NOW)
    # A refused charge records nothing.
    assert budget.spent_usd(now=NOW) == pytest.approx(ceiling - 1.0)
    budget.charge(1.0, now=NOW)
    assert budget.remaining_usd(now=NOW) == 0.0
    with pytest.raises(budget.BudgetExceeded):
        budget.charge(0.01, now=NOW)


def test_month_rollover_resets_meter():
    budget.charge(10.0, now=NOW)
    nxt = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
    assert budget.spent_usd(now=nxt) == 0.0
    assert budget.can_spend(30.0, now=nxt)


def test_can_spend():
    assert budget.can_spend(30.0, now=NOW)
    assert not budget.can_spend(30.01, now=NOW)


def test_negative_charge_rejected():
    with pytest.raises(ValueError):
        budget.charge(-1.0, now=NOW)
