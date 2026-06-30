"""
MSE tweet scraper.

Modes:
  historical  — pull tweets month-by-month from --since date up to today
  update      — pull tweets since last successful run (falls back to 7 days ago)

State is stored in scraper_state.json so incremental updates know where to resume.
Tweets are deduplicated by ID within each CSV before appending.
"""

import csv
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from Scweet import Scweet
from Scweet.config import ScweetConfig
from Scweet.exceptions import AccountPoolExhausted, RateLimitError

from stocks import MSE_STOCKS

DATA_DIR = Path("data")
STATE_FILE = Path("scraper_state.json")
COMBINED_CSV = DATA_DIR / "mn_finance.csv"  # all tweets land here for easy filtering
QUERY_SLEEP = 5      # seconds between individual query calls
STOCK_SLEEP = 10     # seconds between keyword groups
COOLDOWN_WAIT = 135  # seconds to wait when X rate-limits us (Scweet cooldown = 120s + jitter)


def _get_client() -> Scweet:
    auth = os.environ.get("X_AUTH_TOKEN")
    if not auth:
        raise SystemExit("Set X_AUTH_TOKEN env var first.")
    cfg = ScweetConfig(
        daily_requests_limit=500,
        daily_tweets_limit=10_000,
        requests_per_min=20,   # stay well under X's real 30 RPM cap
        min_delay_s=3.0,
    )
    return Scweet(auth_token=auth, manifest_scrape_on_init=False, config=cfg)


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_seen_ids(csv_path: Path) -> set:
    """Return set of tweet IDs already saved in the CSV."""
    if not csv_path.exists():
        return set()
    seen = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row.get("id") or row.get("tweet_id") or row.get("id_str")
            if tid:
                seen.add(tid)
    return seen


def _tweet_id(tweet: dict) -> str | None:
    return tweet.get("tweet_id") or tweet.get("id") or tweet.get("id_str")


def _append_to_csv(path: Path, tweets: list[dict], seen_ids: set) -> int:
    """Append new (unseen) tweets to CSV. Returns count of rows written."""
    new_tweets = []
    for t in tweets:
        tid = _tweet_id(t)
        if tid and tid in seen_ids:
            continue
        new_tweets.append(t)
        if tid:
            seen_ids.add(tid)

    if not new_tweets:
        return 0

    fieldnames = list(new_tweets[0].keys())
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(new_tweets)
    return len(new_tweets)


def _month_chunks(since: str, until: str) -> list[tuple[str, str]]:
    """Split a date range into (start, end) pairs capped at one calendar month each."""
    fmt = "%Y-%m-%d"
    start = datetime.strptime(since, fmt)
    end = datetime.strptime(until, fmt)
    chunks = []
    cursor = start
    while cursor < end:
        # Advance one month
        if cursor.month == 12:
            next_month = cursor.replace(year=cursor.year + 1, month=1, day=1)
        else:
            next_month = cursor.replace(month=cursor.month + 1, day=1)
        chunk_end = min(next_month, end)
        chunks.append((cursor.strftime(fmt), chunk_end.strftime(fmt)))
        cursor = chunk_end
    return chunks


def _search_with_retry(client: Scweet, **kwargs) -> list[dict]:
    """Call client.search(), waiting out cooldowns with one retry."""
    for attempt in range(2):
        try:
            return client.search(**kwargs)
        except (AccountPoolExhausted, RateLimitError) as exc:
            if attempt == 0:
                print(f"    [cooldown] {exc} — waiting {COOLDOWN_WAIT}s...")
                time.sleep(COOLDOWN_WAIT)
            else:
                raise
    return []


def scrape_stock(
    client: Scweet,
    stock: dict,
    since: str,
    until: str,
    limit: int = 300,
) -> list[dict]:
    """Run all queries for one stock in the given date range."""
    ticker = stock["ticker"]
    all_tweets: list[dict] = []
    for query in stock["queries"]:
        try:
            tweets = _search_with_retry(
                client,
                query=query,
                since=since,
                until=until,
                display_type="Latest",
                limit=limit,
            )
            for t in tweets:
                t["ticker"] = ticker
                t["query_used"] = query
            all_tweets.extend(tweets)
            print(f"    '{query}' → {len(tweets)} tweets")
        except Exception as exc:
            print(f"    '{query}' ERROR: {type(exc).__name__}: {exc}")
        time.sleep(QUERY_SLEEP)
    return all_tweets


def historical_pull(since: str = "2024-01-01") -> None:
    """Pull all tweets from `since` up to today, month by month, into one CSV."""
    client = _get_client()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    chunks = _month_chunks(since, today)
    state = _load_state()
    DATA_DIR.mkdir(exist_ok=True)
    seen_ids = _load_seen_ids(COMBINED_CSV)

    print(f"Historical pull: {since} → {today}  ({len(chunks)} month chunks)")
    print(f"Output → {COMBINED_CSV}\n")

    for group in MSE_STOCKS:
        ticker = group["ticker"]
        total_new = 0

        print(f"[{ticker}] {group['name_en']}")
        for chunk_since, chunk_until in chunks:
            print(f"  {chunk_since} → {chunk_until}")
            tweets = scrape_stock(client, group, since=chunk_since, until=chunk_until)
            written = _append_to_csv(COMBINED_CSV, tweets, seen_ids)
            total_new += written
            time.sleep(STOCK_SLEEP)

        state[ticker] = today
        _save_state(state)
        print(f"  [{ticker}] done — {total_new} new tweets\n")

    print(f"Finished. Total rows in {COMBINED_CSV}: {sum(1 for _ in open(COMBINED_CSV, encoding='utf-8')) - 1}")


def incremental_update() -> None:
    """Pull new tweets since the last recorded run for each keyword group."""
    client = _get_client()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    state = _load_state()
    fallback = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    DATA_DIR.mkdir(exist_ok=True)
    seen_ids = _load_seen_ids(COMBINED_CSV)

    print(f"Incremental update — today: {today}")
    print(f"Output → {COMBINED_CSV}\n")

    for group in MSE_STOCKS:
        ticker = group["ticker"]
        since = state.get(ticker, fallback)
        if since == today:
            print(f"[{ticker}] already up to date, skipping.")
            continue

        print(f"[{ticker}] {group['name_en']}  since {since}")
        tweets = scrape_stock(client, group, since=since, until=today)
        written = _append_to_csv(COMBINED_CSV, tweets, seen_ids)

        state[ticker] = today
        _save_state(state)
        print(f"  → {written} new tweets\n")
        time.sleep(STOCK_SLEEP)
