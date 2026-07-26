"""Monthly API spending ceiling, enforced in code (constitution: Safety rails).

All LLM (or otherwise metered) calls must route through charge(). When the
ceiling would be exceeded, BudgetExceeded is raised and callers degrade to
non-LLM operation. Spend is tracked per UTC calendar month in
state/budget.json, which is committed so the system has memory across runs.
"""

from __future__ import annotations

import datetime as _dt

from . import config, state

STATE_FILE = "budget.json"


class BudgetExceeded(Exception):
    pass


def _month(now: _dt.datetime | None = None) -> str:
    now = now or _dt.datetime.now(_dt.timezone.utc)
    return now.strftime("%Y-%m")


def ceiling_usd() -> float:
    return float(config.load()["budget"]["monthly_ceiling_usd"])


def _load(now: _dt.datetime | None = None) -> dict:
    data = state.load(STATE_FILE, default={})
    month = _month(now)
    if data.get("month") != month:
        # New month: reset the meter, remember the previous month for the
        # monthly summary.
        data = {
            "month": month,
            "spent_usd": 0.0,
            "previous": {
                "month": data.get("month"),
                "spent_usd": data.get("spent_usd", 0.0),
            }
            if data.get("month")
            else None,
        }
    return data


def spent_usd(now: _dt.datetime | None = None) -> float:
    return float(_load(now)["spent_usd"])


def remaining_usd(now: _dt.datetime | None = None) -> float:
    return max(0.0, ceiling_usd() - spent_usd(now))


def can_spend(estimated_usd: float, now: _dt.datetime | None = None) -> bool:
    return spent_usd(now) + max(0.0, estimated_usd) <= ceiling_usd()


def charge(cost_usd: float, note: str = "", now: _dt.datetime | None = None) -> float:
    """Record spend. Raises BudgetExceeded (without recording) if the charge
    would cross the ceiling. Returns total spent this month."""
    if cost_usd < 0:
        raise ValueError("cost_usd must be >= 0")
    data = _load(now)
    if data["spent_usd"] + cost_usd > ceiling_usd():
        raise BudgetExceeded(
            f"charge of ${cost_usd:.4f} would exceed monthly ceiling "
            f"${ceiling_usd():.2f} (spent ${data['spent_usd']:.4f})"
        )
    data["spent_usd"] = round(data["spent_usd"] + cost_usd, 6)
    state.save(STATE_FILE, data)
    return data["spent_usd"]
