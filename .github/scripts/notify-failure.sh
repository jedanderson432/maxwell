#!/usr/bin/env bash
#
# Failure notification with signature-keyed dedup and rotation.
#
# The original version searched for the oldest open Issue whose title merely
# began with "MAXWELL failure: <workflow>" and appended to it forever. Issue #1
# therefore swallowed 26 comments spanning a single root cause, and would have
# swallowed every unrelated future failure too -- one thread, no signal.
#
# This version keys the Issue on the *failure signature* (the set of steps that
# actually failed, or an explicit signature the caller passes), so two different
# breakages get two different threads. A thread is retired rather than grown
# without bound:
#   - older than ROTATE_AFTER_DAYS -> close and open a fresh one, because a
#     three-week-old thread is archaeology, not an alarm;
#   - more than MAX_COMMENTS comments -> same.
#
# Usage: notify-failure.sh --workflow <name> [--signature <text>] [--detail <text>]
#                          [--dry-run]
# Env:   GH_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_SERVER_URL
#        NOTIFY_FIXTURE  test-only: JSON standing in for the open-Issue lookup,
#                        so the four decision paths below can be exercised
#                        without touching a real repo (tests/test_notify.py).
set -euo pipefail

MAX_COMMENTS=5
ROTATE_AFTER_DAYS=7
LABEL="maxwell-failure"

WORKFLOW=""
SIGNATURE=""
DETAIL=""
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --workflow)  WORKFLOW="$2"; shift 2 ;;
    --signature) SIGNATURE="$2"; shift 2 ;;
    --detail)    DETAIL="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    *) echo "notify-failure: unknown argument '$1'" >&2; exit 2 ;;
  esac
done
[ -n "$WORKFLOW" ] || { echo "notify-failure: --workflow is required" >&2; exit 2; }

run_url="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"

# Derive the signature from the steps that failed in this run. The notifying
# step is still running, so it cannot appear in its own signature.
if [ -z "$SIGNATURE" ]; then
  SIGNATURE=$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}/jobs" \
    --jq '[.jobs[].steps[]? | select(.conclusion == "failure") | .name] | unique | join(" + ")' \
    2>/dev/null || true)
fi
[ -n "$SIGNATURE" ] || SIGNATURE="unclassified failure"
# Keep titles searchable and within GitHub's limits.
SIGNATURE=$(printf '%s' "$SIGNATURE" | tr '\n' ' ' | cut -c1-120)

TITLE="MAXWELL failure: ${WORKFLOW} — ${SIGNATURE}"
export TITLE
BODY="${run_url}

Workflow: \`${WORKFLOW}\`
Signature: \`${SIGNATURE}\`
Seen: $(date -u +%FT%TZ)"
[ -z "$DETAIL" ] || BODY="${BODY}

${DETAIL}"

if [ "$DRY_RUN" != 1 ]; then
  gh label create "$LABEL" --color B60205 \
    --description "Automated MAXWELL failure notification" >/dev/null 2>&1 || true
fi

# Newest open Issue with this exact title. Exact match, not prefix: a different
# signature must not land in this thread.
if [ -n "${NOTIFY_FIXTURE:-}" ]; then
  # Test-only: the literal "none" stands for "no matching open Issue".
  existing="$NOTIFY_FIXTURE"
  [ "$existing" = "none" ] && existing=""
else
  existing=$(gh api "repos/${GITHUB_REPOSITORY}/issues?state=open&per_page=100" \
    --jq '[.[] | select(has("pull_request") | not) | select(.title == env.TITLE)
           | {number, created_at, comments}]
          | sort_by(.created_at) | reverse | .[0] // empty')
fi

create_new() {
  local extra="${1:-}"
  local number
  if [ "$DRY_RUN" = 1 ]; then echo "DRY"; return; fi
  number=$(gh issue create --title "$TITLE" --body "${BODY}${extra}" \
    --label "$LABEL" --json number --jq .number 2>/dev/null) \
    || number=$(gh issue create --title "$TITLE" --body "${BODY}${extra}" \
         --json number --jq .number)
  echo "$number"
}

if [ -z "$existing" ]; then
  n=$(create_new)
  echo "DECISION=create title=${TITLE}"
  echo "notify-failure: opened #${n} for '${SIGNATURE}'"
  exit 0
fi

# Parsed without system jq: gh's --jq is built into gh, but a bare `jq`
# is not guaranteed on every runner. The object is gh's own projection of
# exactly {number, created_at, comments}, so these patterns are safe.
number=$(printf '%s' "$existing" | sed -n 's/.*"number":[[:space:]]*\([0-9]*\).*/\1/p')
created=$(printf '%s' "$existing" | sed -n 's/.*"created_at":[[:space:]]*"\([^"]*\)".*/\1/p')
comments=$(printf '%s' "$existing" | sed -n 's/.*"comments":[[:space:]]*\([0-9]*\).*/\1/p')
age_days=$(( ( $(date -u +%s) - $(date -u -d "$created" +%s) ) / 86400 ))

reason=""
if [ "$age_days" -gt "$ROTATE_AFTER_DAYS" ]; then
  reason="it is ${age_days} days old (limit ${ROTATE_AFTER_DAYS})"
elif [ "$comments" -ge "$MAX_COMMENTS" ]; then
  reason="it has reached ${comments} comments (cap ${MAX_COMMENTS})"
fi

if [ -z "$reason" ]; then
  echo "DECISION=comment issue=${number} comments=${comments} age_days=${age_days}"
  if [ "$DRY_RUN" != 1 ]; then
    gh issue comment "$number" --body "$BODY" >/dev/null
  fi
  echo "notify-failure: commented on #${number} ($((comments + 1))/${MAX_COMMENTS} comments, ${age_days}d old)"
  exit 0
fi

# Rotate: the old thread is retired and a fresh one opened, so the alarm is
# always about the failure happening now.
echo "DECISION=rotate issue=${number} comments=${comments} age_days=${age_days} reason=${reason}"
new=$(create_new "

Rotated from #${number}, which was closed because ${reason}.")
if [ "$DRY_RUN" != 1 ]; then
  gh issue comment "$number" --body \
    "Rotating this thread: ${reason}. Still failing — continued in #${new}." >/dev/null
  gh issue close "$number" --reason "not planned" >/dev/null
fi
echo "notify-failure: rotated #${number} -> #${new} (${reason})"
