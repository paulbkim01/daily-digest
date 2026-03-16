#!/usr/bin/env python3
"""sweep.py — Deterministic operations for the research sweep pipeline.

Handles all mechanical work (math, filtering, formatting, file I/O) so LLM
agents only do judgment work (searching, scoring, summarizing).

Subcommands:
    seen     Extract URLs from the most recent digest (dedup set)
    score    Calculate weighted scores, assign verdicts
    dedup    Remove seen URLs and failed items
    batch    Split items into scoring batches
    format   Generate markdown digest from passed items
    save     Write markdown to file with collision detection
    coverage Merge scanner coverage manifests into summary report
    pipeline Chain: score → dedup → format → save
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

# ── Constants ────────────────────────────────────────────────────────────────

WEIGHTS = {"R": 1.5, "Q": 1.0, "N": 1.5, "A": 1.0, "S": 1.0}
WEIGHT_DIVISOR = sum(WEIGHTS.values())  # 6.0
PASS_THRESHOLD = 3.5
MUST_READ_THRESHOLD = 4.5
BATCH_TRIGGER = 50
BATCH_SIZE = 20

CATEGORIES = [
    "AI Labs & Models",
    "Developer Tools & IDEs",
    "Engineering & Infrastructure",
    "Research Papers",
    "MLOps & ML Systems",
    "Agents & Frameworks",
    "Video & Audio",
    "Market & Funding",
]

DIGEST_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-(\d+))?\.md$")
URL_RE = re.compile(r"https?://[^\s)\]>\"]+")

# Resolve paths relative to the project root (where this script lives),
# not the caller's working directory.
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DIGESTS_DIR = str(PROJECT_ROOT / "digests")


# ── Core functions ───────────────────────────────────────────────────────────

def find_latest_digest(digests_dir: Path) -> Path | None:
    candidates = []
    if not digests_dir.is_dir():
        return None
    for f in digests_dir.iterdir():
        m = DIGEST_RE.match(f.name)
        if m:
            candidates.append((m.group(1), int(m.group(2) or 0), f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(URL_RE.findall(text)))  # unique, order-preserved


def calc_weighted(scores: dict) -> float:
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS) / WEIGHT_DIVISOR, 2)


def assign_verdict(weighted: float) -> str:
    if weighted >= MUST_READ_THRESHOLD:
        return "MUST READ"
    if weighted >= PASS_THRESHOLD:
        return "PASS"
    return "FAIL"


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip().rstrip("/").lower())
    # Strip tracking params
    params = parse_qs(parsed.query)
    clean_params = {k: v for k, v in params.items()
                    if k not in {"utm_source", "utm_medium", "utm_campaign",
                                 "utm_content", "utm_term", "ref", "source", "via"}}
    # Rebuild without fragment, with cleaned params
    clean = urlunparse((
        parsed.scheme,
        parsed.netloc.removeprefix("www."),
        parsed.path.removesuffix("/index.html"),
        parsed.params,
        urlencode(clean_params, doseq=True) if clean_params else "",
        "",  # no fragment
    ))
    return clean


def dedup_items(items: list[dict], seen: set[str]) -> list[dict]:
    normalized_seen = {normalize_url(u) for u in seen}
    return [
        it for it in items
        if it.get("verdict") != "FAIL"
        and normalize_url(it.get("url", "")) not in normalized_seen
    ]


def truncate_by_score(items: list[dict], max_count: int) -> list[dict]:
    """Sort by weighted score descending and take top N items."""
    if max_count <= 0:
        return items
    sorted_items = sorted(items, key=lambda x: x.get("weighted", 0), reverse=True)
    return sorted_items[:max_count]


def split_batches(items: list) -> list[list]:
    if len(items) <= BATCH_TRIGGER:
        return [items]
    return [items[i:i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]


def group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for it in items:
        cat = it.get("category", "Uncategorized")
        groups.setdefault(cat, []).append(it)
    return groups


def format_item(item: dict) -> str:
    s = item.get("scores", {})
    score_str = f"R:{s.get('R',0)} Q:{s.get('Q',0)} N:{s.get('N',0)} A:{s.get('A',0)} S:{s.get('S',0)}"
    weighted = item.get("weighted", 0)
    summary = item.get("tldr") or item.get("summary", "")
    lines = [
        f"- **{item.get('title', 'Untitled')}** ({weighted})",
        f"  {item.get('author', 'Unknown')} | {item.get('date', '')}",
        f"  {item.get('url', '')}",
        f"  {summary}",
        f"  Scores: {score_str}",
    ]
    return "\n".join(lines)


def format_digest(
    items: list[dict],
    date_str: str,
    scanned: int,
    state_of_world: str = "",
    action_items: str = "",
    sweep_num: int | None = None,
    coverage: dict | None = None,
) -> str:
    groups = group_by_category(items)
    must_reads = [it for it in items if it.get("verdict") == "MUST READ"]
    passed = len(items)
    mr_count = len(must_reads)

    sections = [f"# Research Digest — {date_str}", ""]

    # MUST READ section
    sections.append("## MUST READ (score >= 4.5)")
    sections.append("")
    if must_reads:
        must_reads.sort(key=lambda x: x.get("weighted", 0), reverse=True)
        for it in must_reads:
            sections.append(format_item(it))
            sections.append("")
    else:
        sections.append("No items scored above 4.5.")
        sections.append("")

    # Category sections
    for cat in CATEGORIES:
        sections.append(f"## {cat}")
        sections.append("")
        cat_items = [it for it in groups.get(cat, []) if it.get("verdict") != "MUST READ"]
        cat_items.sort(key=lambda x: x.get("weighted", 0), reverse=True)
        if cat_items:
            for it in cat_items:
                sections.append(format_item(it))
                sections.append("")
        else:
            sections.append("No items passed the quality threshold.")
            sections.append("")

    # State of the World
    sections.append("## State of the World")
    sections.append("")
    sections.append(state_of_world if state_of_world else "[To be synthesized by LLM]")
    sections.append("")

    # Action Items
    sections.append("## Top 3 Action Items")
    sections.append("")
    sections.append(action_items if action_items else "[To be generated by LLM]")
    sections.append("")

    # Footer
    sweep_tag = f" (sweep #{sweep_num})" if sweep_num else ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    sections.append("---")
    footer_line = f"Items scanned: {scanned} | Passed: {passed} | Must-reads: {mr_count}"
    if coverage:
        total = coverage.get("total_sources", 0)
        visited = coverage.get("sources_visited", 0)
        pct = coverage.get("coverage_pct", 0)
        by_status = coverage.get("by_status", {})
        missed_parts = []
        for status in ("timeout", "error", "no_response"):
            count = by_status.get(status, 0)
            if count:
                missed_parts.append(f"{count} {status.replace('_', ' ')}")
        missed_str = f" ({', '.join(missed_parts)})" if missed_parts else ""
        missed_total = total - visited
        footer_line += f"\nSources: {visited}/{total} visited ({pct:.0f}%) | {missed_total} missed{missed_str}"
    sections.append(footer_line)
    sections.append(f"Generated: {now} UTC{sweep_tag}")
    sections.append("")

    return "\n".join(sections)


def next_filename(digests_dir: Path, date_str: str) -> Path:
    base = digests_dir / f"{date_str}.md"
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = digests_dir / f"{date_str}-{counter}.md"
        if not candidate.exists():
            return candidate
        counter += 1


# ── Subcommand handlers ─────────────────────────────────────────────────────

def cmd_seen(args):
    digests_dir = Path(args.digests_dir)
    latest = find_latest_digest(digests_dir)
    if not latest:
        json.dump({"seen": [], "source_file": None}, sys.stdout, indent=2)
        return
    text = latest.read_text(encoding="utf-8")
    urls = extract_urls(text)
    json.dump({"seen": urls, "source_file": latest.name}, sys.stdout, indent=2)


def cmd_score(args):
    items = json.load(sys.stdin)
    for it in items:
        scores = it.get("scores", {})
        w = calc_weighted(scores)
        it["weighted"] = w
        it["verdict"] = assign_verdict(w)
    json.dump(items, sys.stdout, indent=2)


def cmd_dedup(args):
    items = json.load(sys.stdin)
    seen = set()
    if args.seen_file:
        with open(args.seen_file) as f:
            data = json.load(f)
            seen = set(data.get("seen", []))
    result = dedup_items(items, seen)
    if args.max:
        result = truncate_by_score(result, args.max)
    json.dump(result, sys.stdout, indent=2)


def cmd_batch(args):
    items = json.load(sys.stdin)
    batches = split_batches(items)
    json.dump(batches, sys.stdout, indent=2)


def _load_coverage(path: str | None) -> dict | None:
    if not path:
        return None
    with open(path) as f:
        return json.load(f)


def cmd_format(args):
    data = json.load(sys.stdin)
    # Accept either a plain list or {"items": [...], "meta": {...}}
    if isinstance(data, list):
        items = data
        meta = {}
    else:
        items = data.get("items", [])
        meta = data.get("meta", {})

    if args.max:
        items = truncate_by_score(items, args.max)

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scanned = args.scanned or meta.get("scanned", 0)
    state = args.state_of_world or meta.get("state_of_world", "")
    actions = args.action_items or meta.get("action_items", "")
    sweep_num = args.sweep_num or meta.get("sweep_num")

    coverage = _load_coverage(args.coverage_file)
    md = format_digest(items, date_str, scanned, state, actions, sweep_num, coverage)
    sys.stdout.write(md)


def cmd_save(args):
    digests_dir = Path(args.digests_dir)
    digests_dir.mkdir(parents=True, exist_ok=True)
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = next_filename(digests_dir, date_str)
    content = sys.stdin.read()
    filepath.write_text(content, encoding="utf-8")
    json.dump({"path": str(filepath)}, sys.stdout, indent=2)


def cmd_pipeline(args):
    """Chain: score → dedup → format → save."""
    items = json.load(sys.stdin)

    # Score
    for it in items:
        scores = it.get("scores", {})
        it["weighted"] = calc_weighted(scores)
        it["verdict"] = assign_verdict(it["weighted"])

    # Dedup
    digests_dir = Path(args.digests_dir)
    latest = find_latest_digest(digests_dir)
    seen = set()
    if latest:
        seen = set(extract_urls(latest.read_text(encoding="utf-8")))
    items = dedup_items(items, seen)

    # Truncate
    if args.max:
        items = truncate_by_score(items, args.max)

    # Coverage
    coverage = _load_coverage(args.coverage_file)

    # Format
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scanned = args.scanned or 0
    md = format_digest(items, date_str, scanned, sweep_num=args.sweep_num, coverage=coverage)

    # Save
    digests_dir.mkdir(parents=True, exist_ok=True)
    filepath = next_filename(digests_dir, date_str)
    filepath.write_text(md, encoding="utf-8")

    # Report
    must_reads = sum(1 for it in items if it.get("verdict") == "MUST READ")
    result = {"path": str(filepath), "passed": len(items), "must_reads": must_reads}
    json.dump(result, sys.stderr, indent=2)
    sys.stderr.write("\n")


def cmd_coverage(args):
    """Merge scanner coverage manifests into a summary report."""
    manifests = json.load(sys.stdin)
    if not isinstance(manifests, list):
        manifests = [manifests]

    all_sources: dict[str, dict] = {}
    for manifest in manifests:
        cov = manifest.get("coverage")
        if not cov:
            continue
        scanner = cov.get("scanner", "unknown")
        for name, info in cov.get("sources", {}).items():
            all_sources[name] = {**info, "scanner": scanner}

    by_status: dict[str, int] = {}
    for info in all_sources.values():
        status = info.get("status", "no_response")
        by_status[status] = by_status.get(status, 0) + 1

    total = len(all_sources) or args.total_sources or 0
    visited = by_status.get("ok", 0) + by_status.get("empty", 0)
    pct = round(visited / total * 100, 1) if total else 0

    missed = [
        {"name": name, "scanner": info.get("scanner"), "status": info.get("status"), "error": info.get("error")}
        for name, info in all_sources.items()
        if info.get("status") not in ("ok", "empty")
    ]

    report = {
        "total_sources": total,
        "sources_visited": visited,
        "coverage_pct": pct,
        "by_status": by_status,
        "missed_sources": missed,
    }

    # Save to file if requested
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")

    json.dump(report, sys.stdout, indent=2)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic operations for research sweep pipeline"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # seen
    p = sub.add_parser("seen", help="Extract URLs from most recent digest")
    p.add_argument("--digests-dir", default=DEFAULT_DIGESTS_DIR)
    p.set_defaults(func=cmd_seen)

    # score
    p = sub.add_parser("score", help="Calculate weighted scores (stdin: JSON array)")
    p.set_defaults(func=cmd_score)

    # dedup
    p = sub.add_parser("dedup", help="Remove seen URLs and failed items (stdin: JSON)")
    p.add_argument("--seen-file", help="JSON file from 'seen' subcommand")
    p.add_argument("--max", type=int, default=0, help="Max items to keep (0 = no cap)")
    p.set_defaults(func=cmd_dedup)

    # batch
    p = sub.add_parser("batch", help="Split items into scoring batches (stdin: JSON)")
    p.set_defaults(func=cmd_batch)

    # format
    p = sub.add_parser("format", help="Generate markdown digest (stdin: JSON)")
    p.add_argument("--date", help="Digest date (YYYY-MM-DD)")
    p.add_argument("--scanned", type=int, help="Total items scanned")
    p.add_argument("--state-of-world", help="State of the World text")
    p.add_argument("--action-items", help="Top 3 action items text")
    p.add_argument("--sweep-num", type=int, help="Sweep number for footer")
    p.add_argument("--max", type=int, default=0, help="Max items to keep (0 = no cap)")
    p.add_argument("--coverage-file", help="Coverage JSON file for footer stats")
    p.set_defaults(func=cmd_format)

    # save
    p = sub.add_parser("save", help="Save markdown with collision detection (stdin: md)")
    p.add_argument("--digests-dir", default=DEFAULT_DIGESTS_DIR)
    p.add_argument("--date", help="Digest date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_save)

    # coverage
    p = sub.add_parser("coverage", help="Merge scanner coverage manifests (stdin: JSON)")
    p.add_argument("--total-sources", type=int, default=94, help="Total expected sources")
    p.add_argument("--output", help="Save report to this file path")
    p.set_defaults(func=cmd_coverage)

    # pipeline
    p = sub.add_parser("pipeline", help="Full pipeline: score→dedup→format→save")
    p.add_argument("--digests-dir", default=DEFAULT_DIGESTS_DIR)
    p.add_argument("--date", help="Digest date (YYYY-MM-DD)")
    p.add_argument("--scanned", type=int, default=0, help="Total items scanned")
    p.add_argument("--sweep-num", type=int, help="Sweep number")
    p.add_argument("--max", type=int, default=0, help="Max items to keep (0 = no cap)")
    p.add_argument("--coverage-file", help="Coverage JSON file for footer stats")
    p.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
