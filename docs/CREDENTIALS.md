# Credentials MAXWELL needs (supply once)

Add each as a **GitHub Actions secret** in `jedanderson432/maxwell`
(Settings → Secrets and variables → Actions → New repository secret), or
run:

```bash
gh secret set HF_TOKEN --repo jedanderson432/maxwell
```

(prompts for the value; repeat per secret). Every adapter skips cleanly
when its secret is absent, so these can arrive in any order.

| Secret | Where to get it | Notes |
|---|---|---|
| `HF_TOKEN` | huggingface.co → Settings → Access Tokens | Create account (suggest username `jedanderson432`; `jedanderson` is taken). Fine-grained token with write access to your namespace, or a classic `write` token. |
| `ZENODO_SANDBOX_TOKEN` | sandbox.zenodo.org → Applications → Personal access tokens | Separate account from production Zenodo. Scopes: `deposit:write` + `deposit:actions`. Sandbox round-trip is required before production runs. |
| `ZENODO_TOKEN` | zenodo.org → Applications → Personal access tokens | Scopes: `deposit:write` + `deposit:actions`. You already have a Zenodo account (existing essay DOIs). |
| `IA_ACCESS_KEY_ID` | https://archive.org/account/s3.php | Archive.org account required. |
| `IA_SECRET_ACCESS_KEY` | https://archive.org/account/s3.php | Same page as above. |
| `ANTHROPIC_API_KEY` | console.anthropic.com | **Not needed until Phase 3** (no LLM calls in Phases 1–2). |
| `NPM_TOKEN` | npmjs.com | **Not needed**: npm publish is a one-time manual step with your OTP (docs/RUNBOOK_MCP.md); no CI publishing planned. |

Also one-time, not a secret: the npm OTP + GitHub browser login for the
MCP publication — see docs/RUNBOOK_MCP.md.

The kill switch is the repository **variable** `MAXWELL_ENABLED`
(true/false), already configured. Set it to `false` to halt all workflows:

```bash
gh variable set MAXWELL_ENABLED --repo jedanderson432/maxwell --body false
```
