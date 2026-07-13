#!/usr/bin/env bash
# Export Chrome cookies for x.com to a Netscape-format cookies file via yt-dlp.
# Triggers a macOS keychain prompt for "Chrome Safe Storage" - user must click Allow.
# Usage: export_cookies.sh [output_path]  (default /tmp/x-cookies.txt)
set -euo pipefail

OUT="${1:-/tmp/x-cookies.txt}"

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "ERROR: yt-dlp not found. Install with: brew install yt-dlp" >&2
  exit 127
fi

# --skip-download avoids fetching media; we only need the cookie jar extraction.
# || true: yt-dlp may emit "no video" warnings; the cookies file is still written.
yt-dlp --cookies-from-browser chrome --cookies "$OUT" \
  --skip-download "https://x.com" >/dev/null 2>&1 || true

if [[ -s "$OUT" ]]; then
  chmod 600 "$OUT"
  echo "OK cookies exported to $OUT ($(wc -l < "$OUT") lines)"
else
  echo "ERROR: cookies file empty or missing at $OUT" >&2
  exit 1
fi
