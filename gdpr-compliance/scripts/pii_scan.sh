#!/usr/bin/env bash
# GDPR lead finder: grep-based, over-reports on purpose. Hits are leads to read, not findings.
# Usage: pii_scan.sh <repo-root> [file ...]   (files restrict the scan, e.g. a diff's changed files)
set -uo pipefail

ROOT="${1:-.}"; shift || true
FILES=("$@")
MAX="${PII_SCAN_MAX:-40}"   # max hits shown per section

EXCL=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=build
      --exclude-dir=coverage --exclude-dir=.toolchain --exclude-dir=vendor --exclude-dir=.next
      --exclude-dir=test --exclude-dir=tests --exclude-dir=__tests__ --exclude-dir=artifacts
      --exclude-dir=cache --exclude-dir=typechain-types --exclude="*.min.js" --exclude="*.map"
      --exclude="*.test.*" --exclude="*.spec.*" --exclude="*.lock" --exclude="package-lock.json")
INC=(--include="*.ts" --include="*.tsx" --include="*.js" --include="*.mjs" --include="*.cjs"
     --include="*.jsx" --include="*.py" --include="*.go" --include="*.rb" --include="*.php"
     --include="*.html" --include="*.vue" --include="*.svelte")

scan() { # scan <title> <regex> [extra grep flags]
  local title="$1" re="$2"; shift 2
  echo; echo "## $title"
  local out
  if [ ${#FILES[@]} -gt 0 ]; then
    out=$(grep -HnIE "$@" "$re" "${FILES[@]}" 2>/dev/null)
  else
    out=$(grep -rnIE "${EXCL[@]}" "${INC[@]}" "$@" "$re" "$ROOT" 2>/dev/null)
  fi
  if [ -z "$out" ]; then echo "(none)"; return; fi
  local n; n=$(printf '%s\n' "$out" | wc -l | tr -d ' ')
  printf '%s\n' "$out" | sed "s#^$ROOT/##" | cut -c1-220 | head -n "$MAX"
  [ "$n" -gt "$MAX" ] && echo "... $n hits total (PII_SCAN_MAX=$MAX)"
}

echo "# GDPR lead scan: $ROOT"
echo "Generated $(date -u +%Y-%m-%dT%H:%MZ). Leads only; read each in context."

scan "1. Personal data in log lines" \
  '(console\.(log|info|warn|error|debug)|logger\.[a-z]+|log\.(info|warn|error|debug)|print\()[^;]*(email|e_mail|\.name\b|fullName|firstName|lastName|iban|phone|mobile|address|birth|dob|passport|ssn|taxId|vatId|\bip\b|req\.body|err(or)?\.response|\.body\b)' -i
scan "2. Personal data in URLs / query strings" \
  '(searchParams\.(set|append)|params\.(set|append)|[?&](email|name|phone|iban)=)[^;]*(email|name|phone|iban|address)' -i
scan "3. Browser storage writes" \
  '(localStorage|sessionStorage)\.setItem|indexedDB\.open|document\.cookie\s*='
scan "4. Server-set cookies" \
  '(Set-Cookie|res\.cookie\(|setCookie\(|cookies\.set\()' -i
scan "5. Trackers / analytics / error reporting" \
  '(@sentry/|sentry\.io|posthog|mixpanel|segment\.(io|com)|amplitude\.com|@amplitude|google-analytics|googletagmanager|gtag\(|plausible\.io|hotjar|fullstory|datadoghq|dd-trace|newrelic|logrocket|clarity\.ms|widget\.intercom)' -i
scan "6. IP address / device fingerprint handling" \
  '(req\.ips?\b|x-forwarded-for|remoteAddress|cf-connecting-ip|headers\[.user-agent.\]|get\(.user-agent.\)|navigator\.userAgent|FingerprintJS|canvas\.toDataURL)' -i
scan "7. External scripts, fonts, iframes in HTML" \
  '<(script|link|iframe|img)[^>]+(src|href)="https?://' -i
scan "8. Delete / erase / export routes" \
  '((router|app|server|fastify)\.delete\(|@Delete\(|method:\s*["'"'"']DELETE|/export|\berase|anonymi[sz]e|purge|retention)' -i
scan "9. Encryption at rest" \
  '(createCipheriv|crypto\.subtle\.encrypt|encrypt\(|AES-|kms|sealed|libsodium)' -i

echo; echo "## 10. Outbound hosts (unique, from source)"
if [ ${#FILES[@]} -gt 0 ]; then
  hosts=$(grep -ohIE 'https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "${FILES[@]}" 2>/dev/null)
else
  hosts=$(grep -rohIE "${EXCL[@]}" "${INC[@]}" 'https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$ROOT" 2>/dev/null)
fi
printf '%s\n' "$hosts" | sed -E 's#https?://##' | grep -vE '^(localhost|127\.|0\.0\.0\.0|example\.(com|org)|www\.w3\.org|schemas\.|json-schema\.org)' \
  | sort | uniq -c | sort -rn | head -n 60
echo
echo "Next: read each lead in context, then run the four sweeps in references/sweep-prompts.md."
