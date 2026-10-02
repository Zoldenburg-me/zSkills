#!/usr/bin/env bash
# Scan a repo's whole history, every PR head and PR/issue text, then merge,
# score and bucket the findings.
# Usage: run.sh [REPO=.] [--sure 0.85] [--floor 0.2] [--no-pr] [--no-score] [--require-typesafe] [--workdir DIR]
# TYPESAFE_API_KEY comes from the environment, else from REPO/.env.
# Prints the workdir on the last line. Workdir defaults to a fresh temp dir:
# outside the repo on purpose, so a report full of leaks is never committed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${LEAKSCAN_BIN:-$HOME/.cache/repo-leak-scan/bin}"
REPO=.; SURE=0.85; FLOOR=0.2; PR=1; SCORE=1; REQUIRE_TS=0; W=""
while (( $# )); do
  case "$1" in
    --sure) SURE=$2; shift ;; --floor) FLOOR=$2; shift ;;
    --no-pr) PR=0 ;; --no-score) SCORE=0 ;; --require-typesafe) REQUIRE_TS=1 ;; --workdir) W=$2; shift ;;
    *) REPO=$1 ;;
  esac; shift
done
REPO="$(cd "$REPO" && git rev-parse --show-toplevel)"
W="${W:-$(mktemp -d "${TMPDIR:-/tmp}/leakscan.XXXXXX")}"; chmod 700 "$W"
log() { printf '\033[1m==> %s\033[0m\n' "$*" >&2; }

slug=$(git -C "$REPO" remote get-url origin 2>/dev/null \
  | sed -E 's#^(git@|ssh://git@|https://)([^/:]+)[/:]##; s#\.git$##') || slug=""

if [[ -n "$slug" ]]; then
  log "refreshing remote branches (prune deleted/rewritten ones)"
  git -C "$REPO" fetch -q --prune origin 2>&1 | tail -2 || true
fi
if (( PR )) && [[ -n "$slug" ]]; then
  log "fetching all PR heads (refs/pull/*/head -> refs/leakscan/pr/*)"
  git -C "$REPO" fetch -q origin '+refs/pull/*/head:refs/leakscan/pr/*' 2>&1 | tail -2 || true
  log "fetching PR/issue text for $slug"
  python3 "$HERE/fetch_pr_text.py" "$slug" "$W/pr-text" || echo "PR text skipped" >&2
fi
cleanup_refs() { git -C "$REPO" for-each-ref --format='delete %(refname)' refs/leakscan/ | git -C "$REPO" update-ref --stdin; }
trap cleanup_refs EXIT

if [[ -x "$BIN/gitleaks" ]]; then
  log "gitleaks: every commit on every ref"
  # unredacted into the 0700 workdir, then masked in place straight away
  "$BIN/gitleaks" git "$REPO" --log-opts="--all" --no-banner --exit-code 0 --log-level error \
    --report-format json --report-path "$W/gitleaks.json" >&2
  python3 "$HERE/triage.py" sanitize-gitleaks "$W/gitleaks.json"
  if [[ -d "$W/pr-text" ]]; then
    "$BIN/gitleaks" dir "$W/pr-text" --no-banner --exit-code 0 --log-level error \
      --report-format json --report-path "$W/gitleaks-pr.json" >&2
    python3 "$HERE/triage.py" sanitize-gitleaks "$W/gitleaks-pr.json"
  fi
else
  echo "gitleaks not installed ($BIN): secrets NOT scanned by gitleaks" >&2
fi

if [[ -x "$BIN/trufflehog" ]]; then
  log "trufflehog: detect + verify against providers"
  # file:// clones every ref, including the refs/leakscan/pr/* fetched above
  "$BIN/trufflehog" git "file://$REPO" --json --no-update --results=verified,unknown,unverified 2>/dev/null \
    | python3 "$HERE/triage.py" sanitize-trufflehog > "$W/trufflehog.jsonl"
  [[ -d "$W/pr-text" ]] && "$BIN/trufflehog" filesystem "$W/pr-text" --json --no-update \
    --results=verified,unknown,unverified 2>/dev/null \
    | python3 "$HERE/triage.py" sanitize-trufflehog > "$W/trufflehog-pr.jsonl"
else
  echo "trufflehog not installed ($BIN): secrets NOT verified" >&2
fi

# exposure: what a stranger can download today vs what only this clone has
git -C "$REPO" rev-list --remotes=origin > "$W/reach-branches.txt" 2>/dev/null || : > "$W/reach-branches.txt"
git -C "$REPO" rev-list --glob='refs/leakscan/*' > "$W/reach-prrefs.txt" 2>/dev/null || : > "$W/reach-prrefs.txt"

log "private info + disclosure candidates"
python3 "$HERE/scan_private.py" "$REPO" "$W/private.jsonl" ${PR:+--pr-text "$W/pr-text"} >&2

log "local .env values vs history (zero false positives)"
python3 "$HERE/env_crosscheck.py" "$REPO" "$W/envcheck.jsonl" --pr-text "$W/pr-text" >&2

log "merge"
python3 "$HERE/triage.py" merge "$W" >&2
if (( SCORE )); then
  if [[ -z "${TYPESAFE_API_KEY:-}" && -f "$REPO/.env" ]]; then
    TYPESAFE_API_KEY="$(grep -E '^TYPESAFE_API_KEY=' "$REPO/.env" | head -1 | cut -d= -f2- | sed -E "s/^[\"']//; s/[\"']\$//")"
    [[ -n "$TYPESAFE_API_KEY" ]] && export TYPESAFE_API_KEY && echo "TypeSafe key loaded from $REPO/.env" >&2
  fi
  if (( REQUIRE_TS )) && [[ -z "${TYPESAFE_API_KEY:-}" ]]; then
    echo "--require-typesafe: no TYPESAFE_API_KEY in env or $REPO/.env; stopping before scoring" >&2; exit 2
  fi
  log "score (TypeSafe)"
  python3 "$HERE/triage.py" score "$W" --repo "${slug:-$(basename "$REPO")}" >&2
fi
python3 "$HERE/triage.py" report "$W" --sure "$SURE" --floor "$FLOOR" >&2
echo "$W"
