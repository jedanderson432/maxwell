"""Transient failures are absorbed; real failures alarm on the first attempt.

"I want the alarm, not the flakes": a 503 must not page anyone until the
retries are exhausted, and a 401 must not be slept on four times first.
"""

import requests

from src.lib import http


def _resp(status):
    r = requests.Response()
    r.status_code = status
    return r


def test_transient_statuses_retry_then_raise(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)
    calls = []

    def boom():
        calls.append(1)
        raise requests.HTTPError("503 Service Unavailable", response=_resp(503))

    try:
        http.retry_transient(boom, what="thing", retries=3)
    except RuntimeError as exc:
        assert "after 4 attempts" in str(exc)
    else:
        raise AssertionError("should have raised")
    assert len(calls) == 4


def test_transient_that_recovers_returns_value(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise requests.ConnectionError("connection reset")
        return "ok"

    assert http.retry_transient(flaky, what="thing") == "ok"
    assert state["n"] == 3


def test_real_failure_raises_immediately(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda _s: pytest_fail())
    calls = []

    def unauthorized():
        calls.append(1)
        raise requests.HTTPError("401 Unauthorized", response=_resp(401))

    try:
        http.retry_transient(unauthorized, what="thing")
    except requests.HTTPError:
        pass
    else:
        raise AssertionError("should have re-raised the original error")
    assert len(calls) == 1, "a 401 must not be retried"


def pytest_fail():
    raise AssertionError("sleep must not be called for a non-transient failure")


def test_transient_status_tuple_is_shared():
    from src.distribute.zenodo_deposit import ZenodoClient

    assert ZenodoClient.RETRY_STATUS is http.TRANSIENT_STATUS
    assert 504 in http.TRANSIENT_STATUS and 400 not in http.TRANSIENT_STATUS
