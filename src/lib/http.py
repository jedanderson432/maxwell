"""Polite HTTP client: identified user agent, rate limit, retries with backoff."""

from __future__ import annotations

import time

import requests

from . import config

# Statuses that mean "the server is briefly unwell", not "the request is
# wrong". Only these are retried; a 400/401/403/404 is a real failure and must
# surface immediately rather than being slept on four times. Kept here so the
# ingest, Zenodo and HF paths all agree on what "transient" means.
TRANSIENT_STATUS = (429, 500, 502, 503, 504)

_last_request_at = 0.0


def _throttle() -> None:
    global _last_request_at
    rps = float(config.load().get("rate_limit_rps", 4.0))
    min_interval = 1.0 / rps if rps > 0 else 0.0
    wait = _last_request_at + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def get(url: str, *, retries: int = 3, timeout: int = 60, ok_404: bool = False) -> requests.Response | None:
    """GET with throttle and retry. Returns None on 404 when ok_404 is set."""
    headers = {"User-Agent": config.load()["user_agent"]}
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        _throttle()
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 404 and ok_404:
                return None
            if resp.status_code in TRANSIENT_STATUS:
                raise requests.HTTPError(f"{resp.status_code} for {url}")
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:  # includes HTTPError above
            last_exc = exc
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"GET {url} failed after {retries + 1} attempts: {last_exc}")


def _is_transient(exc: BaseException) -> bool:
    """True when exc looks like a blip worth retrying rather than a real bug.

    Deliberately conservative: matches connection/timeout errors and the
    TRANSIENT_STATUS codes wherever the library surfaced them (huggingface_hub
    wraps them in its own exception types, so the status is matched textually
    as a fallback rather than by isinstance alone).
    """
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status is not None:
        return status in TRANSIENT_STATUS
    text = str(exc)
    return any(str(code) in text for code in TRANSIENT_STATUS) and "Error" in type(exc).__name__


def retry_transient(fn, *, what: str, retries: int = 4):
    """Call fn(), retrying only transient failures with exponential backoff.

    Real failures (auth, validation, missing repo) raise on the first attempt
    so the workflow alarms immediately; blips are absorbed silently and only
    alarm once the retries are exhausted.
    """
    last: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            if not _is_transient(exc):
                raise
            last = exc
            if attempt < retries:
                delay = 2**attempt
                print(f"[retry] {what}: transient {type(exc).__name__}; "
                      f"retrying in {delay}s ({attempt + 1}/{retries})")
                time.sleep(delay)
    raise RuntimeError(f"{what} failed after {retries + 1} attempts: {last}")
