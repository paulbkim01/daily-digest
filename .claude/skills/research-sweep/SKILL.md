---
name: research-sweep
version: 1.0.0
description: |
  Run a full research sweep across 90+ tracked AI/ML sources. Fans out parallel scanner
  agents by tier, collects and deduplicates results, scores items against a quality rubric,
  and produces a publication-quality markdown digest with "State of the World" synthesis
  and action items. Use this skill whenever the user wants to run a research sweep, generate
  a digest, check what's new in AI/ML, or asks for a weekly research roundup. Also triggers
  when the user says things like "what happened this week in AI", "scan all sources",
  "run the pipeline", or "make me a digest".
---

# Research Sweep Orchestrator

Run a full research sweep across all tracked sources. Fans out to scanner subagents,
collects results, scores them, and produces a digest.

## Tools

- `sweep.py` — deterministic operations (scoring math, filtering, dedup, coverage, formatting, file I/O)
- `feed_parser.py` — RSS/Atom feed fetcher (fetches structured article lists from `feeds.json`)
- LLM agents handle judgment work only (searching, scoring 1-5, summarizing, synthesizing)

## Instructions

**IMPORTANT:** Always run Python scripts from the repo root (where `sweep.py` lives).
Prefix all bash commands with `cd $(git rev-parse --show-toplevel) &&` to avoid working directory issues.

Follow these steps exactly:

### Step 0: Collect user input and load context

**Run configuration:** Use AskUserQuestion to ask the user for these sweep parameters:
1. **Timeframe** — how far back to scan? (e.g. "24 hours", "7 days", "30 days"). Default: "7 days"
2. **Max articles** — cap for final digest (0 = no cap). Default: 0
3. **Scanner timeout** — max seconds per scanner. Default: 300

Then write the config non-interactively (always cd to repo root first):
```bash
cd $(git rev-parse --show-toplevel) && python3 input.py --timeframe '{timeframe}' --max-articles {max_articles} --timeout {timeout}
```
This writes the config to `/tmp/sweep-config.json`. Read that file and use:
- `timeframe` — pass to all scanners (replaces the hardcoded "12 months")
- `max_articles` — cap the final digest to this many items (after scoring/filtering)
- `timeout_seconds` — max time per scanner subagent

**Source registry:** Read `research-sweep-prompt.md` (in the repo root) and extract the
Source Registry section (Tiers 1-8). This is the single source of truth for all sources.

**Previous digest (dedup):** Run:
```bash
cd $(git rev-parse --show-toplevel) && python3 sweep.py seen
```
This outputs a JSON seen set of URLs from the most recent digest.

### Step 1: Fan out scanners (parallel subagents)

Launch 15 scanner subagents in two waves using the Agent tool. For each scanner, build
the prompt by combining its assignment below with the actual source names/URLs from
the registry in Step 0.

All scanner prompts MUST include these shared rules:

```
SCANNER RULES:
- FEED-FIRST DISCOVERY (MANDATORY):
  1. Run: python3 feed_parser.py fetch --tier {TIERS} --since {timeframe}
  2. Use feed results as your PRIMARY article list (verified URLs, structured data)
  3. Use WebSearch ONLY for sources where feed_url is null or the feed returned 0 items
     (check feeds.json to see which sources lack feeds)
  4. Merge feed + WebSearch results into your final JSON array
- RETURN FORMAT — Return an envelope, not a plain array:
  {
    "items": [...],
    "coverage": {
      "scanner": "{scanner_name}",
      "sources": {
        "Source Name": {"items_found": N, "status": "ok|empty|timeout|error", "error": "..."}
      }
    }
  }
  Status values: ok (visited, found items), empty (visited, nothing new),
  timeout (scanner ran out of time), error (fetch failed with reason).
- Each item: {"title", "url", "author", "date", "summary", "source_tier", "source_name"}
- Only include items from the last {timeframe} (from sweep-config.json).
- URL RULES: See `research-sweep-prompt.md` Rules section. Every URL must point to the
  specific article page. No blog indexes, homepages, or category pages. Use WebFetch or
  Playwright to find correct links. Omit items where you can't find the direct URL.
- WRITING RULES (MANDATORY):
  No AI vocabulary ("delve", "landscape", "paradigm", "leverage", etc.).
  Write like a sharp analyst talking to a peer. Full rules: humanizer/SKILL.md.
```

**Wave 1 (8 scanners, launch all in parallel):**

**S1 — AI Labs (Frontier)** (sonnet)
Sources: Anthropic, OpenAI, DeepMind, Meta AI (4 sources)
Tiers: 1 (partial)

**S2 — AI Labs (Challengers)** (haiku)
Sources: Microsoft Research, Mistral, Cohere, xAI (4 sources)
Tiers: 1 (partial)

**S3 — AI Tooling (IDEs)** (sonnet)
Sources: Cursor, Windsurf/Codeium, Vercel, Replit, GitHub (5 sources)
Tiers: 2 (partial)

**S4 — AI Tooling (Frameworks)** (haiku)
Sources: LangChain, LlamaIndex, Hugging Face (3 sources)
Tiers: 2 (partial)

**S5 — Communities (Social)** (haiku)
Sources: HN, Reddit (5 subs), dev.to, Lobsters (8 sources)
Tiers: 4 (partial)
Focus on: AI/ML discussions, developer tooling debates, trending projects

**S6 — Communities (Newsletters)** (haiku)
Sources: GitHub Trending, Product Hunt, The Gradient, Import AI, The Batch, Marvelous MLOps, ML Engineer Newsletter (7 sources)
Tiers: 4 (partial)

**S7 — Research & Papers** (sonnet)
Sources: HF Daily Papers, arXiv (cs.AI, cs.CL, cs.SE), Semantic Scholar, Papers With Code (6 sources)
Tiers: 5

**S8 — Eng Blogs (Cloud/Infra)** (haiku)
Sources: Cloudflare, AWS Architecture, AWS ML, DigitalOcean, Akamai, Supabase (6 sources)
Tiers: 3 (partial)

**Wave 2 (7 scanners, launch immediately after Wave 1 — no wait):**

**S9 — Eng Blogs (Product)** (haiku)
Sources: Airbnb, Discord, Netflix, Uber, Stripe, Spotify, Figma, Linear, Shopify (9 sources)
Tiers: 3 (partial)

**S10 — MLOps (Infra/Serving)** (haiku)
Sources: Modal, BentoML, Replicate, Anyscale/Ray, Outerbounds (5 sources)
Tiers: 3b (partial)

**S11 — MLOps (Observability)** (haiku)
Sources: W&B, Arize, Evidently, ZenML, Tecton (5 sources)
Tiers: 3b (partial)

**S12 — MLOps (Applied)** (haiku)
Sources: Databricks, DoorDash, Pinterest, MLOps Community (4 sources)
Tiers: 3b (partial)

**S13 — Individuals (LLM/Agents)** (sonnet)
Sources: Simon Willison, Karpathy, swyx, Hamel, Harrison Chase, Jim Fan, Jason Wei (7 sources)
Tiers: 6 (partial)

**S14 — Individuals (ML Eng)** (haiku)
Sources: Lilian Weng, Eugene Yan, Chip Huyen, Vicki Boykis, Shreya Shankar, Jacopo Tagliabue, Goku Mohandas (7 sources)
Tiers: 6 (partial)

**S15 — Media & Market** (sonnet)
Sources: 10 YouTube/podcast channels + a16z, TechCrunch AI, Bloomberg Tech, CB Insights (14 sources)
Tiers: 7 + 8
For each item, also return: `"format": "video|podcast|article"`
For YouTube/podcast pages that need JS rendering, use the Playwright skill.

**Model distribution:** 5 Sonnet (S1, S3, S7, S13, S15 — high-judgment tiers), 10 Haiku (straightforward scraping).

### Step 2: Collect, merge coverage, deduplicate, and batch

Merge all scanner results into a single JSON array. Each scanner returns an envelope
with `items` and `coverage`. Extract items from all envelopes and merge.

**Coverage report:** Collect all coverage envelopes and run:
```bash
cd $(git rev-parse --show-toplevel) && echo '$ALL_ENVELOPES_JSON' | python3 sweep.py coverage --output /tmp/coverage.json
```
This merges coverage manifests and saves the report. If a scanner returned a plain array
(no envelope), the orchestrator wraps it with `coverage: null`.

Remove duplicates (same story from multiple sources — keep the primary source).
If a scanner returned zero results, note it but continue.

If there are many items, use `sweep.py batch` to split for parallel scoring:
```bash
cd $(git rev-parse --show-toplevel) && echo '$MERGED_JSON' | python3 sweep.py batch
```

### Step 3: Score each item (sonnet subagent)

Launch scoring subagent(s) — one per batch if batched. Each scorer receives a JSON
array and must return a JSON array with `scores` and `category` added to each item:

```
Read the scoring rubric from `research-sweep-prompt.md` (Scoring Rubric section).
Score each item 1-5 on: R (Relevance), Q (Quality), N (Novelty), A (Actionability), S (Signal/Noise).

Also assign:
- category: one of the categories defined in `sweep.py` CATEGORIES list
- tldr: 1-2 sentence summary (for items you'd score >= 3.5)

Return as JSON array. Each item must have: all original fields + {"scores": {"R": N, "Q": N, "N": N, "A": N, "S": N}, "category": "...", "tldr": "..."}

Be ruthless. Most items should score below 3.5. Reserve 4.5+ for genuinely exceptional content.
```

### Step 4: Compute scores, filter, and format

Run the deterministic pipeline on the scored JSON:
```bash
cd $(git rev-parse --show-toplevel) && echo '$SCORED_JSON' | python3 sweep.py score | python3 sweep.py dedup --seen-file /tmp/seen.json --max $MAX_ARTICLES > /tmp/passed.json
```

Pass `--max` only when `max_articles` from config is > 0. When 0, omit `--max` (no cap).

This calculates weighted averages, assigns PASS/FAIL/MUST READ verdicts, removes
previously seen URLs, and optionally truncates to top N by score.

### Step 5: Check language preference

Read `.claude/lang.conf`. If it contains `ko`, all prose content (TL;DRs, State of the World,
Action Items) must be written in Korean. Apply the korean-translator skill
(`.claude/skills/korean-translator/SKILL.md`) for style conventions. Keep section headings,
score labels, metadata, and URLs in English. If `lang.conf` is missing or `en`, write in English.

### Step 6: Generate "State of the World" and "Action Items"

Review the passed items in `/tmp/passed.json` and write:
- **State of the World:** 3-5 sentence synthesis of dominant themes
- **Top 3 Action Items:** Concrete, ranked by urgency and impact

Write in the language determined in Step 5.

**WRITING STYLE:** Apply humanizer rules (`.claude/skills/humanizer/SKILL.md`).
No AI vocabulary, no promotional language. Write like a sharp analyst talking to a peer.

### Step 7: Format and save

```bash
cd $(git rev-parse --show-toplevel) && cat /tmp/passed.json | python3 sweep.py format --scanned $TOTAL --date $(date +%Y-%m-%d) --state-of-world "$STATE" --action-items "$ACTIONS" --coverage-file /tmp/coverage.json | python3 sweep.py save
```

Or use the `pipeline` subcommand for Steps 4+7 combined:
```bash
cd $(git rev-parse --show-toplevel) && echo '$SCORED_JSON' | python3 sweep.py pipeline --scanned $TOTAL --coverage-file /tmp/coverage.json
```

If `max_articles > 0` in config, add `--max $MAX_ARTICLES` to the command.

The coverage file enriches the digest footer with source visit stats:
```
Items scanned: 156 | Passed: 42 | Must-reads: 6
Sources: 78/94 visited (83%) | 16 missed (10 timeout, 4 error, 2 no response)
```

Also save full coverage report as `digests/YYYY-MM-DD.coverage.json`.

Print the final summary to the user: must-read count, top 3 action items, coverage stats, and file path.
