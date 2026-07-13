# Design: get-x-recent-posts skill

**Date:** 2026-07-13
**Status:** Approved (pending spec review)
**Related skill:** `.claude/skills/get-x-broadcast-audio/`

## Goal

Produce a JSONL dump of posts from the last N hours (default 24, configurable) for a list of X accounts, then generate a narrative markdown summary with inline post links for every claim.

## Non-goals

- Streaming/real-time monitoring (this is a one-shot dump per run).
- Fetching retweets of external accounts as standalone records (retweets are captured only as a `retweetOf` reference on the amplifying account's record).
- Media download (no image/video bytes saved; only URLs in the schema).
- Official X API integration (deferred; cookie-GraphQL chosen instead).

## Invocation

```
/get-x-recent-posts [--hours 24] [--max-per-account 800] <url|handle> [<url|handle> ...]
```

- Inputs accept full URLs (`https://x.com/yeonwoo1102`), `@handle`, or bare `handle`. Normalized to `handle` internally.
- `--hours` default 24. Cutoff = `now - hours` (UTC). Pagination stops when a tweet's `createdAt` predates the cutoff.
- `--max-per-account` default 800. Safety cap to bound runtime when an account is extremely high-volume within the window.

## Architecture

```
parent agent
  |-- parse args -> [handle, ...]
  |-- export_cookies.sh once          (Chrome keychain Allow prompt)
  |-- for each handle (PARALLEL generalPurpose subagents):
  |      fetch_account.py <handle> --hours N --cookies /tmp/x-cookies.txt
  |        -> output/<handle>-<run>.jsonl
  |-- merge.py output/<handle>-<run>.jsonl (CLI arg order)
  |      -> output/posts-<run>.jsonl
  |-- summariser subagent
         reads output/posts-<run>.jsonl
         -> output/summary-<run>.md
```

`<run>` = `YYYYMMDD-HHMM` UTC at run start, so re-runs don't clobber.

## Components

### `SKILL.md`
Workflow, invocation, schema, summariser prompt, troubleshooting, and the GraphQL `queryId`/`features` capture instructions for when the endpoint breaks.

### `scripts/export_cookies.sh`
```bash
set -euo pipefail
yt-dlp --cookies-from-browser chrome --cookies "${1:-/tmp/x-cookies.txt}" \
  --skip-download "https://x.com" >/dev/null 2>&1 || true
```
Reuses the exact auth path as `get-x-broadcast-audio` (same macOS keychain Allow prompt). `--skip-download` avoids fetching media; `|| true` because yt-dlp may warn about no media.

### `scripts/fetch_account.py`
Single-account fetcher. Steps:
1. Load Netscape cookies file -> extract `auth_token` and `ct0`.
2. Build `requests.Session` with web-client headers:
   - `authorization: Bearer <web bearer>` (well-known public web bearer, hardcoded constant).
   - `x-csrf-token: <ct0>`, `x-twitter-auth-type: OAuth2Session`, `x-twitter-active-user: yes`.
   - `x-client-transaction-id: <random hex>`, realistic `User-Agent`, `Referer: https://x.com/<handle>`.
   - `Cookie:` header rebuilt from all `x.com`/`api.x.com` cookies.
3. Resolve `screen_name -> rest_id` via `UserByScreenName` GraphQL.
4. Page `UserTweetsAndReplies` via `cursor` until `createdAt < cutoff` OR `max-per-account` hit. 1.5s sleep between pages.
5. Normalize each tweet to the rich schema (below) and append one JSON line to `output/<handle>-<run>.jsonl`.
6. Print a one-line summary: `handle=<handle> count=<n> range=<earliest>..<latest> wrote=<path>`.

`queryId` and `features` are loaded from `scripts/query_config.json` so they can be updated without editing Python.

### `scripts/merge.py`
Concatenates per-account JSONL files in the order accounts were passed on the CLI -> `output/posts-<run>.jsonl`. Validates each line parses as JSON; skips/counts invalid lines. Prints `merged=<path> lines=<n> invalid=<n>`.

### `scripts/query_config.json`
```json
{
  "bearer": "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=...",
  "userByScreenName": {"queryId": "...", "features": {...}},
  "userTweetsAndReplies": {"queryId": "...", "features": {...}}
}
```

## JSONL schema (rich)

One line per tweet, UTF-8, deterministic key order:

```json
{
  "id": "2076151238404571136",
  "createdAt": "2026-07-13T01:23:45.000Z",
  "url": "https://x.com/<handle>/status/<id>",
  "type": "tweet | reply | quote | retweet",
  "text": "full text",
  "inReplyTo": {"userId": "...", "screenName": "...", "statusId": "..."} | null,
  "quoteOf": {"userId": "...", "screenName": "...", "statusId": "...", "text": "..."} | null,
  "retweetOf": {"userId": "...", "screenName": "...", "statusId": "..."} | null,
  "hashtags": ["..."],
  "cashtags": ["..."],
  "expandedUrls": ["https://..."],
  "mediaUrls": ["https://..."],
  "lang": "en",
  "metrics": {"reply": 0, "retweet": 0, "like": 0, "quote": 0},
  "author": {"id": "...", "screenName": "...", "name": "...", "verified": false}
}
```

`type` derivation (uses raw `legacy.conversation_id` read internally, not emitted):
- `retweetOf` non-null -> `retweet`.
- `quoteOf` non-null -> `quote`.
- `inReplyTo` non-null and `inReplyTo.statusId != legacy.conversation_id` -> `reply` (self-replies threading from the author's own prior tweet count as `tweet`).
- else `tweet`.

## Summariser

One `generalPurpose` subagent reads `output/posts-<run>.jsonl` and writes `output/summary-<run>.md`.

Output structure:
- **Run metadata**: handles, `--hours`, total tweet count, time range.
- **Themes**: cross-account narratives in the window.
- **Per-account highlights**: notable posts with a one-line takeaway, each hyperlinked to `https://x.com/<handle>/status/<id>`.
- **Cross-account**: shared narratives and divergences.
- **Tickers/topics**: surfaced from `cashtags`/`hashtags` with frequency.
- **Unresolved / follow-ups**: open questions for the analyst.

Rule: every factual claim about a specific post must be an inline markdown link to that post's `url`. No link = no claim.

## Concurrency & failure isolation

- One subagent per account, launched in parallel (single message, multiple `Task` calls).
- A subagent whose `fetch_account.py` exits non-zero writes nothing (or a partial file is discarded); the parent logs the failure and continues. Merge skips missing per-account files but lists them in run metadata.
- No shared mutable state during fetch (per-account files only). Merge is single-threaded in the parent.

## Auth & ToS

- Cookies come from the user's own logged-in Chrome via the same keychain flow as `get-x-broadcast-audio`. The skill does not store credentials beyond the ephemeral `/tmp/x-cookies.txt` (Netscape format, mode 600).
- Hitting private GraphQL with your own session cookies is against X's ToS; documented as a known risk in `SKILL.md`. The skill is for personal/analyst use.

## Key risks & mitigations

| Risk | Mitigation |
|------|------------|
| GraphQL `queryId`/`features` rotate -> 400/403 | `query_config.json` is external; `SKILL.md` documents DevTools capture steps |
| Cookies expired/rotated by Chrome | Re-run re-prompts keychain (same as broadcast skill) |
| High-volume account blows past runtime | `--max-per-account` cap (default 800) |
| Rate limiting / 429 | 1.5s page delay; exponential backoff on 429; abort account after 3 retries |
| Concurrent append races | Avoided by design: per-account files, parent merges |
| `screen_name` suspended/renamed | `UserByScreenName` failure logged; account skipped |

## Verification

```bash
ls -lh output/*-<run>.jsonl output/posts-<run>.jsonl output/summary-<run>.md
wc -l output/posts-<run>.jsonl                              # = sum of per-account lines
python3 -c "import json,sys;[json.loads(l) for l in open('output/posts-<run>.jsonl')]" && echo OK
```

Parent reports: per-account counts, merged line count, invalid line count, summary path, and any skipped accounts.

## Dependencies

- `yt-dlp`, `ffmpeg` already used by `get-x-broadcast-audio` (ffmpeg not strictly needed here but present).
- Python: `requests` (pinned exact version in a `requirements.txt` for the skill, run via `uv run --with requests==<pin>`). No other third-party deps; cookie parsing is a small inline Netscape parser to avoid `browser_cookie3` keychain quirks.

## Open questions (none blocking)

- Whether to later add `--accounts <file>` for watchlist runs (deferred; inline args chosen for v1).
- Whether to capture the raw GraphQL `legacy` blob alongside rich fields (deferred; rich-only chosen for v1).
