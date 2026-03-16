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

3. Search for content from the last 12 months from those sources.

## Output

For each item found, output:
```
- **[Title]** — [URL]
  Author: [name] | Date: [date] | Format: [type]
  Summary: [1 sentence]
```

**URL RULES (MANDATORY — items that violate these are DISCARDED):**
- Every URL MUST point to the specific article, paper, or video — not a blog index, homepage, or section page.
- If you cannot find the direct URL, use WebFetch to visit the source and locate the correct link.
- If WebFetch fails (JS-heavy pages, dynamic content), use the Playwright skill to navigate and extract links.
  Run: `cd .claude/skills/playwright-skill && node run.js /tmp/scrape-*.js`
- If you still cannot find it, OMIT the item entirely rather than using a generic URL.

**WRITING RULES (MANDATORY):**
- Summaries must sound human-written. No AI vocabulary ("delve", "landscape", "paradigm", etc.).
- Write like a sharp analyst, not a press release. Be direct and specific.

Sort by date (newest first). Skip anything older than 12 months.
