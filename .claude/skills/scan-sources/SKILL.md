---
name: scan-sources
version: 1.0.0
description: |
  Quick-scan a specific source tier for new AI/ML content without running the full sweep.
  Searches a targeted group of sources (AI labs, tooling, engineering blogs, MLOps,
  communities, papers, individuals, media, or market) and returns structured results.
  Use this skill when the user wants to check a specific source group, says things like
  "scan AI labs", "check what's new on engineering blogs", "look at the research papers",
  "any new YouTube content?", "check HN and Reddit", or wants to quickly survey one
  category of sources without running the entire pipeline.
---

# Scan Sources

Quick-scan a specific source tier for new content. Use this to check individual
source groups without running the full sweep.

## Usage

The user specifies a tier: `ai-labs`, `tooling`, `eng-blogs`, `mlops`,
`communities`, `papers`, `individuals`, `media`, `market`, or `all`.

## Instructions

1. **Read the source registry** from `research-sweep-prompt.md` (in the repo root),
   specifically the "Source Registry" section (Tiers 1-8).

2. Based on the tier requested, extract the matching sources:

| Argument      | Registry Tier(s)                              |
|---------------|-----------------------------------------------|
| `ai-labs`     | Tier 1: AI Lab & Model Provider Blogs         |
| `tooling`     | Tier 2: AI Tooling & IDE Companies            |
| `eng-blogs`   | Tier 3: Tech Company Engineering Blogs        |
| `mlops`       | Tier 3b: MLOps & ML Systems Engineering       |
| `communities` | Tier 4: Aggregators & Communities             |
| `papers`      | Tier 5: Research & Papers                     |
| `individuals` | Tier 6: Notable Individuals                   |
| `media`       | Tier 7: YouTube & Podcasts                    |
| `market`      | Tier 8: Financial & Market Intel              |
| `all`         | All tiers, sequentially                       |

3. Check `/tmp/sweep-config.json` for the `timeframe` value. If missing, default to `7 days`.

4. **Feed-first discovery (MANDATORY):** Before using WebSearch, fetch RSS/Atom feeds:
   ```bash
   python3 feed_parser.py fetch --tier {TIER_ID} --since {timeframe}
   ```
   Use feed results as the PRIMARY article list. Only use WebSearch for sources where
   `feed_url` is null in `feeds.json` or the feed returned 0 items. Merge feed + WebSearch
   results together.

5. Search for content within that timeframe from those sources.

## Output

For each item found, output:
```
- **[Title]** — [URL]
  Author: [name] | Date: [date] | Format: [type]
  Summary: [1 sentence]
```

**URL RULES:** See `research-sweep-prompt.md` Rules section. Every URL must point to the
specific article page. No index pages, homepages, or section pages. Use WebFetch or Playwright
to find correct links. Omit items where you can't find the direct URL.

**WRITING RULES:** Apply humanizer rules (`.claude/skills/humanizer/SKILL.md`).
No AI vocabulary. Write direct and specific, like an analyst.

Sort by date (newest first). Skip anything outside the configured timeframe.
