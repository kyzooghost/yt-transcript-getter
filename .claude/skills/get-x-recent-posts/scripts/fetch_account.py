#!/usr/bin/env python3
"""Fetch recent posts for one X account via Chrome-cookie auth + x.com GraphQL.

Self-healing: extracts the bearer token and GraphQL queryIds from x.com's
main.<hash>.js at runtime, so queryId rotation is handled automatically.
The `features` dict is loaded from query_config.json (rotates less often).

Usage:
    fetch_account.py --handle <handle> --hours 24 --max-per-account 800 \
        --cookies /tmp/x-cookies.txt --run <YYYYMMDD-HHMM> --out-dir output
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from urllib.parse import quote

import requests

GRAPHQL_HOST = "https://api.x.com"
WEB_HOME = "https://x.com"
PROXY_URL = ""  # Set at runtime via --proxy-url or X_PROXY_URL env var
SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_CONFIG = json.loads((SCRIPT_DIR / "query_config.json").read_text())
DEFAULT_BEARER = QUERY_CONFIG.get("bearer", "")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

OPERATIONS = ("UserByScreenName", "UserTweetsAndReplies", "UserTweets")


def log(msg: str) -> None:
    print(f"[fetch:{os.environ.get('X_HANDLE','?')}] {msg}", flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


# --- cookies -----------------------------------------------------------------

def load_cookies(path: str) -> dict[str, str]:
    jar = MozillaCookieJar(path)
    jar.load(ignore_discard=True, ignore_expires=True)
    cookies: dict[str, str] = {}
    for c in jar:
        if any(d in (c.domain or "") for d in ("x.com", "twitter.com")):
            cookies[c.name] = c.value
    if "ct0" not in cookies or "auth_token" not in cookies:
        die(f"missing auth_token/ct0 in {path} - is Chrome logged into x.com?")
    return cookies


# --- self-healing config extraction ------------------------------------------

def extract_bearer(js: str) -> str:
    """The web bearer is an AAAAAA... token embedded in main.js."""
    candidates = re.findall(r'(AAAAAAAAAAAAAAAAAAAA[A-Za-z0-9_%=]{20,})', js)
    if not candidates:
        return DEFAULT_BEARER
    # longest, then URL-decode
    best = max(candidates, key=len)
    return best.replace("%3D", "=")


def extract_query_ids(js: str) -> dict[str, str]:
    ids: dict[str, str] = {}
    # Matches: queryId:"abc",operationName:"UserByScreenName"
    for m in re.finditer(r'queryId:"([A-Za-z0-9_\-]+)",operationName:"([A-Za-z]+)"', js):
        qid, op = m.group(1), m.group(2)
        if op in OPERATIONS:
            ids[op] = qid
    return ids


def rewrite_cdn_url(url: str) -> str:
    """Rewrite an absolute CDN URL through the proxy /cdn/ route if PROXY_URL is set."""
    if not PROXY_URL:
        return url
    # https://abs.twimg.com/path -> <PROXY_URL>/cdn/abs.twimg.com/path
    m = re.match(r'https://([a-z0-9.\-]+)(/.+)', url)
    if m:
        return f"{PROXY_URL}/cdn/{m.group(1)}{m.group(2)}"
    return url


def fetch_web_config(session: requests.Session, handle: str) -> tuple[str, dict[str, str]]:
    """Fetch x.com profile HTML, then main.<hash>.js to extract bearer + queryIds."""
    html = session.get(f"{WEB_HOME}/{handle}", timeout=30).text
    scripts = re.findall(r'(https://[a-z0-9.\-]+/responsive-web/client-web/main\.[a-z0-9]+\.js)', html)
    if not scripts:
        # fall back to API host endpoint listing; some builds use api.twimg.com
        scripts = re.findall(r'(https://[a-z0-9.\-]+/client-web/main\.[a-z0-9]+\.js)', html)
    if not scripts:
        die("could not find main.<hash>.js in x.com HTML - did the SPA markup change?")
    bearer = DEFAULT_BEARER
    ids: dict[str, str] = {}
    for url in dict.fromkeys(scripts):  # dedupe, preserve order
        fetch_url = rewrite_cdn_url(url)
        try:
            js = session.get(fetch_url, timeout=60).text
        except requests.RequestException as e:
            log(f"failed to fetch {fetch_url}: {e}")
            continue
        if not bearer or bearer == DEFAULT_BEARER:
            bearer = extract_bearer(js) or bearer
        ids.update(extract_query_ids(js))
        if len(ids) >= 2 and bearer and bearer != DEFAULT_BEARER:
            break
    missing = [op for op in OPERATIONS[:2] if op not in ids]
    if missing:
        die(f"could not extract queryIds for {missing} from main.js")
    return bearer, ids


# --- graphql calls -----------------------------------------------------------

def graphql_get(session: requests.Session, bearer: str, query_id: str, op: str,
                variables: dict, features: dict, handle: str, method: str = "GET") -> dict:
    body = {
        "variables": json.dumps(variables, separators=(",", ":")),
        "features": json.dumps(features, separators=(",", ":")),
    }
    url = f"{GRAPHQL_HOST}/graphql/{query_id}/{op}"
    headers = {
        "authorization": f"Bearer {bearer}",
        "x-csrf-token": session.headers["x-csrf-token"],
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en",
        "x-client-transaction-id": f"{random.randrange(16**96):096x}",
        "content-type": "application/json",
        "Referer": f"{WEB_HOME}/{handle}",
        "Origin": WEB_HOME,
    }
    for attempt in range(3):
        if method == "POST":
            # UserTweetsAndReplies is POST-only on x.com (GET returns 404 empty).
            resp = session.post(url, json=body, headers=headers, timeout=30)
        else:
            resp = session.get(url, params=body, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = 2 ** (attempt + 1)
            log(f"429 rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        # 400/401/403/404 - surface body for diagnosis
        die(f"{op} HTTP {resp.status_code} ({method}): {resp.text[:300]}")
    die(f"{op} exhausted retries (429)")


def resolve_user_id(session: requests.Session, bearer: str, ids: dict[str, str],
                    features: dict, handle: str) -> str:
    variables = {"screen_name": handle, "withSafetyModeUserField": True}
    data = graphql_get(session, bearer, ids["UserByScreenName"], "UserByScreenName",
                       variables, features, handle)
    try:
        user = data["data"]["user"]["result"]
        if user.get("__typename") == "UserUnavailable":
            die(f"account @{handle} unavailable: {user.get('reason')}")
        return str(user["rest_id"])
    except (KeyError, TypeError):
        die(f"UserByScreenName unexpected response: {json.dumps(data)[:400]}")


# --- tweet parsing -----------------------------------------------------------

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def parse_created_at(s: str) -> datetime:
    # "Mon Jul 13 03:51:00 +0000 2026"
    parts = s.split()
    # [Dow, Mon, Day, HH:MM:SS, TZ, Year]
    m = MONTHS[parts[1]]
    day = int(parts[2])
    hh, mm, ss = (int(x) for x in parts[3].split(":"))
    year = int(parts[5])
    return datetime(year, m, day, hh, mm, ss, tzinfo=timezone.utc)


def author_from(result: dict, fallback_handle: str = "") -> dict:
    user = result.get("core", {}).get("user_results", {}).get("result", {})
    ucore = user.get("core", {}) or {}
    legacy = user.get("legacy", {}) or {}
    return {
        "id": str(user.get("rest_id", "")),
        "screenName": ucore.get("screen_name", "") or legacy.get("screen_name", "") or fallback_handle,
        "name": ucore.get("name", "") or legacy.get("name", "") or fallback_handle,
        "verified": bool(user.get("is_blue_verified") or legacy.get("verified")),
    }


def ref_summary(result: dict, fallback_handle: str = "") -> dict | None:
    """For quoted/retweeted referenced tweets: minimal info."""
    if not result:
        return None
    if "tweet" in result:
        result = result["tweet"]
    if result.get("__typename") not in ("Tweet", "TweetWithVisibilityResults"):
        return None
    leg = result.get("legacy", {})
    author = author_from(result, fallback_handle)
    return {
        "userId": author["id"],
        "screenName": author["screenName"],
        "statusId": str(result.get("rest_id", "")),
        "text": leg.get("full_text", "")[:280],
    }


def normalize_tweet(result: dict, cutoff: datetime, handle: str) -> dict | None:
    """Map a tweet_results.result dict to the rich schema, or None if it should be skipped."""
    if "tweet" in result:
        result = result["tweet"]
    typename = result.get("__typename", "")
    if typename not in ("Tweet", "TweetWithVisibilityResults"):
        log(f"skipping __typename={typename} id={result.get('rest_id','?')}")
        return None
    tid = str(result.get("rest_id", ""))
    if not tid:
        return None
    leg = result.get("legacy", {})
    created = parse_created_at(leg.get("created_at", "Mon Jan 01 00:00:00 +0000 2000"))
    if created < cutoff:
        return None  # signal caller to treat as out-of-window

    author = author_from(result, handle)
    entities = leg.get("entities", {})
    hashtags = [h["text"] for h in entities.get("hashtags", [])]
    cashtags = [s["text"] for s in entities.get("symbols", [])]
    expanded_urls = [u.get("expanded_url", u.get("url", "")) for u in entities.get("urls", [])]
    media_urls = [m.get("media_url_https", "") for m in entities.get("media", [])
                  if m.get("media_url_https")]

    conv_id = str(leg.get("conversation_id_str", ""))
    in_reply_to = None
    if leg.get("in_reply_to_status_id_str"):
        in_reply_to = {
            "statusId": str(leg["in_reply_to_status_id_str"]),
            "screenName": leg.get("in_reply_to_screen_name", ""),
            "userId": str(leg.get("in_reply_to_user_id_str", "")),
        }

    quote_of = None
    if leg.get("quoted_status_id_str") or leg.get("quoted_status_permalink"):
        qid = str(leg.get("quoted_status_id_str", ""))
        permalink = leg.get("quoted_status_permalink", {}) or {}
        quoted = result.get("quoted_status_result", {}).get("result")
        if quoted:
            quote_of = ref_summary(result.get("quoted_status_result", {}))
            if quote_of:
                quote_of["statusId"] = qid or quote_of["statusId"]
        else:
            quote_of = {
                "statusId": qid,
                "screenName": "",
                "userId": "",
                "text": "",
                "url": permalink.get("expanded", ""),
            }

    retweet_of = None
    rt_result = leg.get("retweeted_status_result", {}).get("result")
    if rt_result:
        retweet_of = ref_summary(rt_result)

    if retweet_of:
        ttype = "retweet"
    elif quote_of:
        ttype = "quote"
    elif in_reply_to and in_reply_to["statusId"] and in_reply_to["statusId"] != conv_id:
        ttype = "reply"
    else:
        ttype = "tweet"

    return {
        "id": tid,
        "createdAt": created.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "url": f"https://x.com/{author['screenName'] or handle}/status/{tid}",
        "type": ttype,
        "text": leg.get("full_text", ""),
        "inReplyTo": in_reply_to,
        "quoteOf": quote_of,
        "retweetOf": retweet_of,
        "hashtags": hashtags,
        "cashtags": cashtags,
        "expandedUrls": expanded_urls,
        "mediaUrls": media_urls,
        "lang": leg.get("lang", ""),
        "metrics": {
            "reply": leg.get("reply_count", 0),
            "retweet": leg.get("retweet_count", 0),
            "like": leg.get("favorite_count", 0),
            "quote": leg.get("quote_count", 0),
        },
        "author": author,
    }


def iter_page_tweets(data: dict) -> tuple[list[dict], str | None]:
    """Return (tweet_result_dicts, bottom_cursor) from a timeline GraphQL response."""
    tweets: list[dict] = []
    bottom_cursor: str | None = None
    try:
        instructions = (data["data"]["user"]["result"]
                        ["timeline_response"]["timeline"]["instructions"])
    except (KeyError, TypeError):
        # some responses nest under .timeline.timeline
        try:
            instructions = (data["data"]["user"]["result"]
                            ["timeline"]["timeline"]["instructions"])
        except (KeyError, TypeError):
            return tweets, None

    for instr in instructions:
        # TimelinePinEntry delivers a single pinned tweet under "entry" (singular).
        pin_entry = instr.get("entry")
        if pin_entry:
            content = pin_entry.get("content", {}) or {}
            ic = content.get("itemContent")
            if ic:
                result = (ic.get("tweet_results", {}) or {}).get("result")
                if result:
                    tweets.append(result)
        for entry in instr.get("entries", []):
            content = entry.get("content", {}) or {}
            etype = content.get("entryType", "") or ""
            ctype = content.get("cursorType", "")
            if ctype or etype.endswith("Cursor"):
                if ctype == "Bottom" or "Bottom" in etype:
                    bottom_cursor = content.get("value") or content.get("cursorValue")
                continue
            item_content = content.get("itemContent")
            if item_content:
                result = (item_content.get("tweet_results", {}) or {}).get("result")
                if result:
                    tweets.append(result)
                continue
            # conversation cluster: moduleItems / items
            for mi in (entry.get("moduleItems") or content.get("items") or []):
                # items can be nested as {item: {itemContent: ...}} or flat {itemContent: ...}
                inner = mi.get("item", mi)
                ic = inner.get("itemContent") or mi.get("itemContent") or mi
                result = (ic.get("tweet_results", {}) or {}).get("result")
                if result:
                    tweets.append(result)
    return tweets, bottom_cursor


# --- main --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--max-per-account", type=int, default=800)
    ap.add_argument("--cookies", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out-dir", default="output")
    ap.add_argument("--proxy-url",
                    default=os.environ.get("X_PROXY_URL", ""),
                    help="Proxy base URL (e.g. https://x-proxy.xxx.workers.dev)")
    args = ap.parse_args()

    os.environ["X_HANDLE"] = args.handle

    # Apply proxy URL to module globals if set.
    global WEB_HOME, GRAPHQL_HOST, PROXY_URL
    if args.proxy_url:
        PROXY_URL = args.proxy_url.rstrip("/")
        WEB_HOME = f"{PROXY_URL}/x"
        GRAPHQL_HOST = f"{PROXY_URL}/api"
        log(f"proxy mode: WEB_HOME={WEB_HOME} GRAPHQL_HOST={GRAPHQL_HOST}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    cookies = load_cookies(args.cookies)

    session = requests.Session()
    # Corporate proxies may MITM TLS with self-signed certs; honour env override.
    # session.verify alone is insufficient in some requests versions, so we
    # monkey-patch .request() to inject verify=False into every call.
    if os.environ.get("X_FETCH_NO_VERIFY", "").lower() in ("1", "true", "yes"):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        _orig_request = session.request
        def _patched_request(*args, **kwargs):
            kwargs.setdefault("verify", False)
            return _orig_request(*args, **kwargs)
        session.request = _patched_request
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-csrf-token": cookies["ct0"],
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
    })
    # Add proxy auth token if configured.
    proxy_token = os.environ.get("X_PROXY_TOKEN", "")
    if proxy_token:
        session.headers["X-Proxy-Token"] = proxy_token

    bearer, ids = fetch_web_config(session, args.handle)
    log(f"extracted bearer={'yes' if bearer else 'no'}, queryIds={list(ids.keys())}")

    user_id = resolve_user_id(session, bearer, ids,
                              QUERY_CONFIG["userByScreenName"]["features"], args.handle)
    log(f"resolved @{args.handle} -> rest_id {user_id}")

    out_path = Path(args.out_dir) / f"{args.handle}-{args.run}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure an empty file exists even when 0 tweets are in-window, so the merge
    # step can distinguish "0 tweets" from a failed fetch.
    out_path.touch()

    count = 0
    cursor = None
    earliest = None
    latest = None
    stop = False
    page = 0
    seen_ids: set[str] = set()
    while count < args.max_per_account and not stop:
        page += 1
        variables = {
            "userId": user_id,
            "count": 40,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }
        if cursor:
            variables["cursor"] = cursor
            variables["cursorType"] = "Bottom"
        data = graphql_get(session, bearer, ids["UserTweetsAndReplies"],
                           "UserTweetsAndReplies", variables,
                           QUERY_CONFIG["userTweetsAndReplies"]["features"], args.handle,
                           method="POST")
        results, next_cursor = iter_page_tweets(data)
        if not results:
            log(f"page {page}: no tweets, stopping")
            break
        with out_path.open("a", encoding="utf-8") as f:
            for result in results:
                rec = normalize_tweet(result, cutoff, args.handle)
                if rec is None:
                    # could be out-of-window (created < cutoff) or tombstone
                    leg = (result.get("legacy") or {})
                    ca = leg.get("created_at")
                    if ca:
                        try:
                            cdt = parse_created_at(ca)
                            if cdt < cutoff:
                                stop = True
                        except Exception:
                            pass
                    continue
                if rec["id"] in seen_ids:
                    continue  # pagination cursor overlap re-delivers tweets
                seen_ids.add(rec["id"])
                f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
                count += 1
                cdt = datetime.strptime(rec["createdAt"], "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc)
                if earliest is None or cdt < earliest:
                    earliest = cdt
                if latest is None or cdt > latest:
                    latest = cdt
                if count >= args.max_per_account:
                    stop = True
                    break
        log(f"page {page}: +{len(results)} results, total emitted {count}, "
            f"has_next={bool(next_cursor)}, stop={stop}")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(1.5)

    range_str = "none"
    if earliest and latest:
        range_str = f"{earliest.strftime('%Y-%m-%dT%H:%M')}..{latest.strftime('%Y-%m-%dT%H:%M')}"
    log(f"handle={args.handle} count={count} range={range_str} wrote={out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
