"""Polite HTTP client: identified user agent, rate limit, retries with backoff."""

from __future__ import annotations

import time

import requests

from . import config

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
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{resp.status_code} for {url}")
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:  # includes HTTPError above
            last_exc = exc
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"GET {url} failed after {retries + 1} attempts: {last_exc}")
