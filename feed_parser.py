#!/usr/bin/env python3
"""feed_parser.py — RSS/Atom feed fetcher for the research sweep pipeline.

Stdlib-only Python CLI. Fetches feeds from feeds.json, parses RSS 2.0 and Atom,
filters by date, and outputs structured JSON matching the scanner schema.

Subcommands:
    fetch     Fetch feeds for a tier, filter by date, output JSON
    validate  Test all feed URLs, report alive/dead
    list      Show sources, optionally filtered by feed availability
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FEEDS_FILE = PROJECT_ROOT / "feeds.json"

# XML namespaces used across RSS/Atom/YouTube feeds
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Domains that need rate limiting
RATE_LIMITED_DOMAINS = {"reddit.com", "www.reddit.com"}
_rate_limit_lock = threading.Lock()


def _maybe_rate_limit(url: str) -> None:
    if any(domain in url for domain in RATE_LIMITED_DOMAINS):
        with _rate_limit_lock:
            time.sleep(0.5)


def load_sources(tiers: list[str] | None = None) -> list[dict]:
    """Load sources from feeds.json, optionally filtered by tier."""
    data = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))
    sources = data["sources"]
    if tiers:
        sources = [s for s in sources if s["tier"] in tiers]
    return sources


def parse_timeframe(timeframe: str) -> datetime:
    """Convert a timeframe string like '7d', '48 hours', '14 days' to a cutoff datetime."""
    timeframe = timeframe.strip().lower()

    # Handle shorthand: 7d, 24h
    if timeframe.endswith("d") and timeframe[:-1].isdigit():
        days = int(timeframe[:-1])
        return datetime.now(timezone.utc) - timedelta(days=days)
    if timeframe.endswith("h") and timeframe[:-1].isdigit():
        hours = int(timeframe[:-1])
        return datetime.now(timezone.utc) - timedelta(hours=hours)

    # Handle "N hours", "N days"
    parts = timeframe.split()
    if len(parts) == 2:
        num = int(parts[0])
        unit = parts[1].rstrip("s")  # normalize "hours" -> "hour"
        if unit == "hour":
            return datetime.now(timezone.utc) - timedelta(hours=num)
        if unit == "day":
            return datetime.now(timezone.utc) - timedelta(days=num)
        if unit == "week":
            return datetime.now(timezone.utc) - timedelta(weeks=num)
        if unit == "month":
            return datetime.now(timezone.utc) - timedelta(days=num * 30)
        if unit == "year":
            return datetime.now(timezone.utc) - timedelta(days=num * 365)

    # Fallback: 7 days
    return datetime.now(timezone.utc) - timedelta(days=7)


def parse_date(date_str: str | None) -> datetime | None:
    """Parse various date formats found in feeds."""
    if not date_str:
        return None
    date_str = date_str.strip()

    # RFC 2822 (standard RSS)
    try:
        return parsedate_to_datetime(date_str)
    except (ValueError, TypeError):
        pass

    # ISO 8601 variants
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None


def fetch_feed(url: str, timeout: int = 15) -> bytes | None:
    """Fetch a feed URL and return raw bytes."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return None


def parse_rss_items(root: ET.Element) -> list[dict]:
    """Parse RSS 2.0 <item> elements."""
    items = []
    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        author = (
            item.findtext("dc:creator", "", NS)
            or item.findtext("author", "")
        ).strip()
        pub_date = item.findtext("pubDate", "").strip()
        description = item.findtext("description", "").strip()

        # Truncate description to something reasonable
        if len(description) > 500:
            description = description[:497] + "..."

        items.append({
            "title": title,
            "url": link,
            "author": author,
            "date": pub_date,
            "summary": description,
        })
    return items


def parse_atom_items(root: ET.Element) -> list[dict]:
    """Parse Atom <entry> elements."""
    items = []
    for entry in root.iter(f"{{{NS['atom']}}}entry"):
        title = (entry.findtext(f"{{{NS['atom']}}}title", "") or "").strip()

        # Atom links: prefer rel="alternate", fall back to first <link>
        link = ""
        for link_el in entry.iter(f"{{{NS['atom']}}}link"):
            href = link_el.get("href", "")
            rel = link_el.get("rel", "alternate")
            if rel == "alternate":
                link = href
                break
            if not link:
                link = href

        author_el = entry.find(f"{{{NS['atom']}}}author")
        author = ""
        if author_el is not None:
            author = (author_el.findtext(f"{{{NS['atom']}}}name", "") or "").strip()

        updated = (
            entry.findtext(f"{{{NS['atom']}}}published", "")
            or entry.findtext(f"{{{NS['atom']}}}updated", "")
        ).strip()

        summary = (
            entry.findtext(f"{{{NS['atom']}}}summary", "")
            or entry.findtext(f"{{{NS['atom']}}}content", "")
            or ""
        ).strip()
        if len(summary) > 500:
            summary = summary[:497] + "..."

        # YouTube-specific: extract video ID
        yt_id = entry.findtext(f"{{{NS['yt']}}}videoId", "")
        if yt_id and "youtube.com" not in link:
            link = f"https://www.youtube.com/watch?v={yt_id}"

        items.append({
            "title": title,
            "url": link,
            "author": author,
            "date": updated,
            "summary": summary,
        })
    return items


def parse_feed(raw: bytes) -> list[dict]:
    """Parse raw XML bytes into a list of item dicts."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    # Detect format: Atom uses {atom namespace}feed as root
    if root.tag == f"{{{NS['atom']}}}feed":
        return parse_atom_items(root)

    # RSS 2.0: root is <rss>, items under <channel>; also handles RDF/RSS 1.0
    return parse_rss_items(root)


def fetch_and_parse(source: dict, cutoff: datetime) -> list[dict]:
    """Fetch a single source's feed and return filtered items."""
    feed_url = source.get("feed_url")
    if not feed_url:
        return []

    _maybe_rate_limit(feed_url)

    raw = fetch_feed(feed_url)
    if raw is None:
        return []

    items = parse_feed(raw)

    # Filter by date and enrich with source metadata
    filtered = []
    for item in items:
        dt = parse_date(item.get("date"))
        if dt and dt < cutoff:
            continue

        item["source_tier"] = source["tier"]
        item["source_name"] = source["name"]
        filtered.append(item)

    return filtered


# ── Subcommands ──────────────────────────────────────────────────────────────

def cmd_fetch(args):
    """Fetch feeds for given tiers, filter by date, output JSON."""
    tiers = [t.strip() for t in args.tier.split(",")] if args.tier else None
    cutoff = parse_timeframe(args.since)

    sources = [s for s in load_sources(tiers) if s.get("feed_url")]
    all_items = []

    def _fetch_one(source):
        items = fetch_and_parse(source, cutoff)
        if args.verbose:
            print(f"  {source['name']}: {len(items)} items", file=sys.stderr)
        return items

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for items in pool.map(_fetch_one, sources):
            all_items.extend(items)

    json.dump(all_items, sys.stdout, indent=2, ensure_ascii=False)


def cmd_validate(args):
    """Test all feed URLs, report alive/dead."""
    sources = load_sources()
    results = {"alive": [], "dead": [], "no_feed": []}
    results_lock = threading.Lock()

    no_feed = [s["name"] for s in sources if not s.get("feed_url")]
    results["no_feed"] = no_feed
    feed_sources = [s for s in sources if s.get("feed_url")]

    def _validate_one(source):
        feed_url = source["feed_url"]
        _maybe_rate_limit(feed_url)
        raw = fetch_feed(feed_url, timeout=10)
        if raw and len(raw) > 100:
            items = parse_feed(raw)
            entry = {"name": source["name"], "url": feed_url, "items": len(items)}
            with results_lock:
                results["alive"].append(entry)
            if args.verbose:
                print(f"  OK  {source['name']} ({len(items)} items)", file=sys.stderr)
        else:
            entry = {"name": source["name"], "url": feed_url}
            with results_lock:
                results["dead"].append(entry)
            if args.verbose:
                print(f"  DEAD  {source['name']}", file=sys.stderr)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(_validate_one, feed_sources))

    summary = {
        "alive": len(results["alive"]),
        "dead": len(results["dead"]),
        "no_feed": len(results["no_feed"]),
        "details": results,
    }
    json.dump(summary, sys.stdout, indent=2)


def cmd_list(args):
    """List sources, optionally filtered."""
    sources = load_sources()

    if args.no_feed:
        sources = [s for s in sources if not s.get("feed_url")]
    elif args.has_feed:
        sources = [s for s in sources if s.get("feed_url")]

    for s in sources:
        feed_status = s.get("feed_url") or "(no feed — WebSearch fallback)"
        print(f"[Tier {s['tier']}] {s['name']}: {feed_status}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RSS/Atom feed fetcher for research sweep pipeline"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # fetch
    p = sub.add_parser("fetch", help="Fetch feeds for a tier, filter by date")
    p.add_argument("--tier", help="Comma-separated tier IDs (e.g. '1,2' or '3b')")
    p.add_argument("--since", default="7d", help="Timeframe filter (e.g. '7d', '48 hours')")
    p.add_argument("--verbose", "-v", action="store_true")
    p.set_defaults(func=cmd_fetch)

    # validate
    p = sub.add_parser("validate", help="Test all feed URLs")
    p.add_argument("--verbose", "-v", action="store_true")
    p.set_defaults(func=cmd_validate)

    # list
    p = sub.add_parser("list", help="List sources")
    p.add_argument("--no-feed", action="store_true", help="Show only sources without feeds")
    p.add_argument("--has-feed", action="store_true", help="Show only sources with feeds")
    p.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
