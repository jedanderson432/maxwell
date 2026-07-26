"""MCP Registry: verify the jedanderson-corpus-mcp listing resolves.

The one-time publish itself is Jed's (npm publish needs his OTP; registry
login is a browser OAuth) — see docs/RUNBOOK_MCP.md. This module checks the
official registry (API v0.1, verified 2026-07-26) so health runs can detect
the listing appearing or vanishing.

Usage: python -m src.distribute.mcp_registry
"""

from __future__ import annotations

import sys

from ..lib import config, http, state

STATE_FILE = "mcp.json"


def check_listing() -> dict | None:
    cfg = config.load()["mcp"]
    name = cfg["server_name"]
    url = f"{cfg['registry_base'].rstrip('/')}/v0.1/servers?search={name}"
    resp = http.get(url)
    data = resp.json()
    for entry in data.get("servers", []):
        server = entry.get("server", entry)
        if server.get("name") == name:
            return server
    return None


def run() -> bool:
    server = check_listing()
    st = {"server_name": config.load()["mcp"]["server_name"]}
    if server:
        st.update({"listed": True, "version": server.get("version")})
        print(f"[mcp] listing OK: {st['server_name']} v{server.get('version')}")
    else:
        st["listed"] = False
        print(f"[mcp] NOT listed yet: {st['server_name']} (npm publish + registry publish pending — see docs/RUNBOOK_MCP.md)")
    state.save(STATE_FILE, st)
    return bool(server)


if __name__ == "__main__":
    listed = run()
    # Not being listed yet is expected pre-publication; never a failure exit.
    sys.exit(0)
