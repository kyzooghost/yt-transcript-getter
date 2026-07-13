---
name: get-x-recent-posts
description: Dump recent posts (last N hours, default 24) for a list of X accounts to JSONL using Chrome-cookie auth against x.com GraphQL, then produce a narrative markdown summary with inline post links per claim. Use when the user wants to collect/summarise recent X/Twitter activity for one or more accounts, e.g. /get-x-recent-posts --hours 24 https://x.com/yeonwoo1102 @waveking1314 or --accounts x/robinhood-accounts.txt.
---

# Get X Recent Posts

Collect recent posts for a list of X accounts into one JSONL file, then summarise with linked claims.

## Usage

```
/get-x-recent-posts [--hours 24] [--max-per-account 800] [--accounts <file>] <url|handle> [<url|handle> ...]
```

- Inputs accept `https://x.com/<handle>`, `@handle`, or bare `handle`.
- `--accounts <file>` reads one URL/handle per line (blank lines and `#` comments ignored). Combine with inline args or use alone.
- `--hours` default 24. `--max-per-account` default 800 (safety cap).

## Prerequisites

- `yt-dlp` (cookies export), `uv` (Python runtime). Chrome logged into x.com.
- macOS keychain Allow prompt appears when cookies are exported - user must Allow.

## Workflow

### 1. Normalise account list

Parse inline args + `--accounts` file(s) into a de-duplicated list of handles (strip `https://x.com/`, `@`, trailing slashes, query strings). Compute `<run>` = `YYYYMMDD-HHMM` UTC.

### 2. Export cookies once

```bash
bash .claude/skills/get-x-recent-posts/scripts/export_cookies.sh /tmp/x-cookies.txt
```

User clicks Allow on the keychain prompt. Cookies are written Netscape-format, mode 600, to `/tmp/x-cookies.txt`.

### 3. Fetch per account in parallel

Launch **one `generalPurpose` subagent per account in parallel** (single message, multiple Task calls). Each subagent runs:

```bash
uv run --with requests==2.32.3 python .claude/skills/get-x-recent-posts/scripts/fetch_account.py \
  --handle <handle> --hours <N> --max-per-account <M> \
  --cookies /tmp/x-cookies.txt --run <run> --out-dir output
```

Each writes `output/<handle>-<run>.jsonl`. A failed account logs and is skipped - it does not abort the run.

### 4. Merge

```bash
uv run python .claude/skills/get-x-recent-posts/scripts/merge.py --run <run> --out-dir output --handles <h1> <h2> ...
```

Concatenates per-account files in handle order -> `output/posts-<run>.jsonl`. Validates JSON; skips/counts invalid lines.

### 5. Summarise

Launch **one summariser subagent** reading `output/posts-<run>.jsonl` -> `output/summary-<run>.md`. Summariser prompt:

> You are an analyst summarising recent X activity across accounts. Read the JSONL (one tweet per line). Produce a narrative markdown report:
> - **Run metadata**: handles, hours, total tweets, time range.
> - **Themes**: cross-account narratives in the window.
> - **Per-account highlights**: notable posts with a one-line takeaway, each hyperlinked to its `url` (`https://x.com/<handle>/status/<id>`).
> - **Cross-account**: shared narratives and divergences.
> - **Tickers/topics**: surfaced from `cashtags`/`hashtags` with counts.
> - **Unresolved / follow-ups**: open questions for the analyst.
>
> Rule: every factual claim about a specific post MUST be an inline markdown link to that post's `url`. No link = no claim. Do not fabricate posts or URLs.

### 6. Verify

```bash
ls -lh output/*-<run>.jsonl output/posts-<run>.jsonl output/summary-<run>.md
wc -l output/posts-<run>.jsonl
uv run --with requests==2.32.3 python -c "import json;[json.loads(l) for l in open('output/posts-<run>.jsonl')]" && echo OK
```

Report per-account counts, merged line count, invalid count, summary path, and any skipped accounts.

## JSONL schema

One line per tweet (UTF-8, deterministic key order):

```json
{"id":"...","createdAt":"2026-07-13T01:23:45.000Z","url":"https://x.com/<handle>/status/<id>","type":"tweet|reply|quote|retweet","text":"...","inReplyTo":{"userId":"...","screenName":"...","statusId":"..."}|null,"quoteOf":{...}|null,"retweetOf":{...}|null,"hashtags":[],"cashtags":[],"expandedUrls":[],"mediaUrls":[],"lang":"en","metrics":{"reply":0,"retweet":0,"like":0,"quote":0},"author":{"id":"...","screenName":"...","name":"...","verified":false}}
```

`type` derivation (uses raw `legacy.conversation_id` read internally, not emitted):
- `retweetOf` non-null -> `retweet`
- `quoteOf` non-null -> `quote`
- `inReplyTo` non-null and `inReplyTo.statusId != legacy.conversation_id` -> `reply`
- else `tweet`

## Self-healing GraphQL config

`fetch_account.py` extracts the bearer token and `queryId`s for `UserByScreenName` and `UserTweetsAndReplies` directly from x.com's `main.<hash>.js` at runtime, so queryId rotation is handled automatically. The `features` dict lives in `scripts/query_config.json` and rotates less often.

### When `features` break (400 with a features error)

1. Open Chrome DevTools on `https://x.com/<handle>` -> Network -> filter `UserTweetsAndReplies`.
2. Click the request -> Payload -> copy the `features` JSON.
3. Replace `scripts/query_config.json` `userTweetsAndReplies.features` (and `userByScreenName.features` from its request).
4. Re-run.

## Auth

Cookies come from your own logged-in Chrome via the same keychain flow as `get-x-broadcast-audio`. The ephemeral `/tmp/x-cookies.txt` is Netscape-format, mode 600, and is not persisted beyond the run.

## Common issues

- **Keychain prompt**: macOS asks for Chrome Safe Storage access - click Allow.
- **401/403**: cookies expired or Chrome rotated them - re-run `export_cookies.sh`.
- **400 features error**: refresh `query_config.json` per above.
- **429 rate limit**: 1.5s page delay + exponential backoff; account aborts after 3 retries.
- **Suspended/renamed handle**: `UserByScreenName` fails -> account skipped, logged in run metadata.
