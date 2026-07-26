# RUNBOOK: publish `jedanderson-corpus-mcp` (one-time, ~10 minutes)

The MCP server is already built and tested in the site repo at `mcp/`.
Publishing needs two things only a human can do: an npm OTP and a GitHub
browser login. Everything below is copy-paste. Verified against current
docs 2026-07-26 (registry API v0.1, schema 2025-12-11).

## Step 1 — add the registry ownership field to package.json

In the **site repo** (`jedanderson432/jedanderson-site`), edit
`mcp/package.json` and add one top-level field (the registry fetches the
published package and requires `mcpName` to exactly match the registry
name):

```json
"mcpName": "io.github.jedanderson432/jedanderson-corpus-mcp",
```

Commit it (this is your edit in your repo — MAXWELL never writes there).

## Step 2 — publish to npm

You need an npmjs.com account (free) with 2FA. From the site repo:

```bash
cd mcp
npm publish --access public --otp=<6-digit code from your authenticator>
```

Verify: https://www.npmjs.com/package/jedanderson-corpus-mcp

## Step 3 — publish to the official MCP Registry

From the `maxwell` repo root (the prepared `server.json` is at
`docs/mcp/server.json`; copy it next to where you run the commands, or run
them in `docs/mcp/`):

Windows (PowerShell) install of the publisher CLI:

```powershell
$arch = if ([System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -eq "Arm64") { "arm64" } else { "amd64" }; Invoke-WebRequest -Uri "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_$arch.tar.gz" -OutFile "mcp-publisher.tar.gz"; tar xf mcp-publisher.tar.gz mcp-publisher.exe; rm mcp-publisher.tar.gz
```

Then:

```bash
./mcp-publisher login github
```

```bash
./mcp-publisher publish
```

(`login github` opens a browser OAuth; it grants publish rights to
`io.github.jedanderson432/*`.)

## Step 4 — verify (MAXWELL does this automatically too)

```bash
python -m src.distribute.mcp_registry
```

or manually:
https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.jedanderson432/jedanderson-corpus-mcp

## Notes

- Keep `version` in `docs/mcp/server.json` exactly equal to the npm
  package version (currently `1.0.0`). Future releases: bump both, re-run
  `npm publish` and `mcp-publisher publish`.
- Secondary registries: PulseMCP ingests the official registry weekly and
  Glama crawls public GitHub — no action needed. Others require manual
  accounts and were skipped (see docs/DECISIONS.md).
