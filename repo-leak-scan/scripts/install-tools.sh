#!/usr/bin/env bash
# Download the latest gitleaks and trufflehog release binaries into a cache dir,
# verifying each archive against the checksums file published in the same release.
# Usage: install-tools.sh [--dry-run]
#   --dry-run  print what would be downloaded (names, URLs, sizes) and exit
set -euo pipefail

BIN_DIR="${LEAKSCAN_BIN:-$HOME/.cache/repo-leak-scan/bin}"
DRY=0; [[ "${1:-}" == "--dry-run" ]] && DRY=1

os=$(uname -s | tr '[:upper:]' '[:lower:]')        # darwin | linux
arch=$(uname -m)
case "$arch" in
  x86_64|amd64) garch=x64;  tarch=amd64 ;;
  arm64|aarch64) garch=arm64; tarch=arm64 ;;
  *) echo "unsupported arch: $arch" >&2; exit 1 ;;
esac

api() { curl -fsSL -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$1/releases/latest"; }

# prints: name url size  for the asset whose name matches $2 (python regex)
pick() {
  python3 -c '
import json,re,sys
rel=json.load(sys.stdin); pat=re.compile(sys.argv[1])
for a in rel["assets"]:
    if pat.fullmatch(a["name"]): print(a["name"], a["browser_download_url"], a["size"])
' "$1"
}

install_one() { # repo tool asset_regex checksum_regex
  local repo=$1 tool=$2 rel asset sums name url size sname surl
  rel=$(api "$repo")
  asset=$(printf '%s' "$rel" | pick "$3")
  sums=$(printf '%s' "$rel" | pick "$4")
  [[ -n "$asset" && -n "$sums" ]] || { echo "$tool: no matching release asset for $os/$arch" >&2; return 1; }
  read -r name url size <<<"$asset"
  read -r sname surl _ <<<"$sums"
  if (( DRY )); then
    printf '%-11s %s  (%s MB)\n            %s\n' "$tool" "$name" "$(( size / 1048576 ))" "$url"
    return
  fi
  local tmp; tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/$name" "$url"
  curl -fsSL -o "$tmp/$sname" "$surl"
  (cd "$tmp" && grep " $name\$" "$sname" | shasum -a 256 -c -) >/dev/null \
    || { echo "$tool: CHECKSUM MISMATCH, not installed" >&2; rm -rf "$tmp"; return 1; }
  tar -xzf "$tmp/$name" -C "$tmp" "$tool"
  mkdir -p "$BIN_DIR"; mv "$tmp/$tool" "$BIN_DIR/$tool"; chmod +x "$BIN_DIR/$tool"
  rm -rf "$tmp"
  echo "$tool: installed $("$BIN_DIR/$tool" --version 2>&1 | head -1) -> $BIN_DIR/$tool"
}

install_one gitleaks/gitleaks gitleaks \
  "gitleaks_[0-9.]+_${os}_${garch}\.tar\.gz" "gitleaks_[0-9.]+_checksums\.txt"
install_one trufflesecurity/trufflehog trufflehog \
  "trufflehog_[0-9.]+_${os}_${tarch}\.tar\.gz" "trufflehog_[0-9.]+_checksums\.txt"
