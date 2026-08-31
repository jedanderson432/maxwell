"""Failure-Issue dedup: signature-keyed, comment-capped, age-rotated.

Issue #1 accumulated 26 comments for a single root cause because the old
notifier appended to the oldest open Issue whose title merely *started with*
"MAXWELL failure: ingest". These exercise the replacement's decision paths
through its --dry-run mode, so no repo is touched.
"""

import datetime as _dt
import json
import shutil
import subprocess

import pytest

SCRIPT = ".github/scripts/notify-failure.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash not available"
)


def _run(fixture, *, signature="Zenodo production", workflow="ingest"):
    env = {
        "PATH": "/usr/bin:/bin",
        "GITHUB_REPOSITORY": "jedanderson432/maxwell",
        "GITHUB_RUN_ID": "1",
        "GITHUB_SERVER_URL": "https://github.com",
        "NOTIFY_FIXTURE": "none" if fixture is None else json.dumps(fixture),
    }
    out = subprocess.run(
        ["bash", SCRIPT, "--workflow", workflow,
         "--signature", signature, "--dry-run"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    decision = [l for l in out.stdout.splitlines() if l.startswith("DECISION=")]
    assert decision, out.stdout
    # reason= is free text with spaces, so keep the raw line alongside the
    # parsed key/value pairs rather than mangling it.
    parsed = dict(
        part.split("=", 1)
        for part in decision[0].split(" reason=")[0].split(" ")
        if "=" in part
    )
    parsed["_line"] = decision[0]
    return parsed


def _days_ago(n):
    return (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=n)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def test_no_matching_issue_opens_one():
    assert _run(None)["DECISION"] == "create"


def test_recent_thread_under_the_cap_gets_a_comment():
    d = _run({"number": 7, "created_at": _days_ago(2), "comments": 2})
    assert d["DECISION"] == "comment"
    assert d["issue"] == "7"


def test_thread_rotates_at_the_comment_cap():
    """Five comments is the cap; the sixth failure opens a fresh thread."""
    d = _run({"number": 7, "created_at": _days_ago(1), "comments": 5})
    assert d["DECISION"] == "rotate"
    assert "cap 5" in d["_line"], d["_line"]


def test_thread_rotates_when_older_than_seven_days():
    d = _run({"number": 7, "created_at": _days_ago(9), "comments": 1})
    assert d["DECISION"] == "rotate"
    assert d["age_days"] == "9"


def test_seven_day_boundary_still_comments():
    d = _run({"number": 7, "created_at": _days_ago(6), "comments": 1})
    assert d["DECISION"] == "comment"


def test_signature_is_part_of_the_title():
    """Two different breakages must not share one thread.

    The title carries the signature, and the lookup matches the title exactly,
    so an unrelated failure in the same workflow cannot land here.
    """
    out = subprocess.run(
        ["bash", SCRIPT, "--workflow", "ingest",
         "--signature", "Archive.org item update", "--dry-run"],
        capture_output=True, text=True, timeout=60,
        env={"PATH": "/usr/bin:/bin", "GITHUB_REPOSITORY": "x/y",
             "GITHUB_RUN_ID": "1", "GITHUB_SERVER_URL": "https://github.com",
             "NOTIFY_FIXTURE": "none"},
    )
    line = next(l for l in out.stdout.splitlines() if l.startswith("DECISION=create"))
    assert line.endswith("Archive.org item update")
    assert "MAXWELL failure: ingest" in line
