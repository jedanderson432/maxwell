"""Global kill switch.

The repository variable MAXWELL_ENABLED is the authoritative switch
(constitution: Safety rails). GitHub workflows gate on it at the job level
AND export it into the environment; every entrypoint calls require_enabled()
as defense in depth. Any value other than the exact string "false"
(case-insensitive) is treated as enabled, so local development works
without the variable set.
"""

from __future__ import annotations

import os
import sys


class Disabled(SystemExit):
    pass


def enabled() -> bool:
    return os.environ.get("MAXWELL_ENABLED", "true").strip().lower() != "false"


def require_enabled() -> None:
    if not enabled():
        print("MAXWELL_ENABLED is false; exiting silently.", file=sys.stderr)
        raise Disabled(0)
