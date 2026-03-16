#!/usr/bin/env python3
"""input.py — Configuration for research sweep runs.

Interactive mode (default): prompts the user for sweep parameters.
Non-interactive mode (--timeframe): accepts CLI args directly.

Writes config to /tmp/sweep-config.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONFIG_PATH = Path("/tmp/sweep-config.json")

TIMEFRAME_PRESETS = {
    "1": ("Past 24 hours", "24 hours"),
    "2": ("Past 48 hours", "48 hours"),
    "3": ("Past week", "7 days"),
    "4": ("Past 2 weeks", "14 days"),
    "5": ("Past month", "30 days"),
    "6": ("Past 3 months", "90 days"),
    "7": ("Past year", "365 days"),
}


def prompt_timeframe() -> str:
    print("\nTimeframe — how far back to scan?")
    for key, (label, _) in TIMEFRAME_PRESETS.items():
        print(f"  {key}) {label}")
    print("  c) Custom (e.g. '300 hours', '10 days')")

    while True:
        choice = input("\nChoice [3]: ").strip() or "3"
        if choice in TIMEFRAME_PRESETS:
            _, value = TIMEFRAME_PRESETS[choice]
            print(f"  → {value}")
            return value
        if choice.lower() == "c":
            custom = input("Enter timeframe (e.g. '300 hours', '10 days'): ").strip()
            if custom:
                print(f"  → {custom}")
                return custom
            print("  Empty input, try again.")
        else:
            print(f"  Unknown option '{choice}', try again.")


def prompt_max_articles() -> int:
    while True:
        raw = input("\nMax articles to include in digest (0 = no cap) [0]: ").strip() or "0"
        try:
            n = int(raw)
            if n < 0:
                print("  Must be 0 or positive.")
                continue
            print(f"  → {n}" if n else "  → no cap")
            return n
        except ValueError:
            print(f"  '{raw}' is not a number, try again.")


def prompt_timeout() -> int:
    while True:
        raw = input("\nMax timeout per scanner in seconds [300]: ").strip() or "300"
        try:
            t = int(raw)
            if t < 10:
                print("  Must be at least 10 seconds.")
                continue
            print(f"  → {t}s")
            return t
        except ValueError:
            print(f"  '{raw}' is not a number, try again.")


def main():
    parser = argparse.ArgumentParser(description="Research sweep configuration")
    parser.add_argument("--timeframe", help="e.g. '7 days', '24 hours', '30 days'")
    parser.add_argument("--max-articles", type=int, help="Max articles in digest (0 = no cap)")
    parser.add_argument("--timeout", type=int, help="Max seconds per scanner")
    args = parser.parse_args()

    # Non-interactive mode: all args provided via CLI
    if args.timeframe is not None:
        config = {
            "timeframe": args.timeframe,
            "max_articles": args.max_articles if args.max_articles is not None else 0,
            "timeout_seconds": args.timeout if args.timeout is not None else 300,
        }
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"Config saved to {CONFIG_PATH}")
        print(json.dumps(config, indent=2))
        return

    # Interactive mode: prompt the user
    if not sys.stdin.isatty():
        print("Error: interactive mode requires a terminal. Use CLI args instead:", file=sys.stderr)
        print("  python3 input.py --timeframe '7 days' [--max-articles 0] [--timeout 300]", file=sys.stderr)
        sys.exit(1)

    print("=" * 50)
    print("  Research Sweep Configuration")
    print("=" * 50)

    timeframe = prompt_timeframe()
    max_articles = prompt_max_articles()
    timeout = prompt_timeout()

    config = {
        "timeframe": timeframe,
        "max_articles": max_articles,
        "timeout_seconds": timeout,
    }

    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"\nConfig saved to {CONFIG_PATH}")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
