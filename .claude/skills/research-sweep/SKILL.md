---
name: research-sweep
version: 1.0.0
description: |
  Run a full research sweep across 80+ tracked AI/ML sources. Fans out parallel scanner
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

`sweep.py` handles all deterministic operations (scoring math, filtering, dedup,
markdown formatting, file I/O). LLM agents handle judgment work only (searching,
scoring 1-5, summarizing, synthesizing).

## Instructions

Follow these steps exactly:

### Step 0: Load context

**Source registry:** Read `research-sweep-prompt.md` (in the repo root) and extract the
Source Registry section (Tiers 1-8). This is the single source of truth for all sources.

**Previous digest (dedup):** Run:
```bash
python3 sweep.py seen
```
This outputs a JSON seen set of URLs from the most recent digest.

### Step 1: Fan out scanners (parallel subagents)

Launch these subagents IN PARALLEL using the Agent tool. For each scanner, build the
prompt by combining its tier assignment below with the actual source names/URLs extracted
from the registry in Step 0.

All scanner prompts MUST include these shared rules:

```
SCANNER RULES:
- Return results as a JSON array. Each item: {"title": "...", "url": "...", "author": "...", "date": "...", "summary": "...", "source_tier": "..."}
- Only include items from the last 12 months.
- URL RULES (MANDATORY — items that violate these are DISCARDED):
  Every URL MUST point to the specific article page, not a blog index, homepage, or category page.
  If you cannot find the direct article URL, use WebFetch to visit the blog and find the correct link.
  If WebFetch fails (JS-heavy pages, dynamic content), use the Playwright skill to navigate to the
  blog and extract article links. Run from: .claude/skills/playwright-skill/
  If you still cannot find it, OMIT the item entirely rather than using a generic URL.
  arXiv links MUST include the paper ID (e.g., /abs/XXXX.XXXXX).
  YouTube links MUST be watch URLs (e.g., youtube.com/watch?v=XXXXX).
  Podcast links MUST be episode-specific, not archive pages.
- WRITING RULES (MANDATORY):
  All summaries must sound human-written. No AI vocabulary: avoid "delve", "landscape",
  "paradigm", "leverage", "robust", "comprehensive", "tapestry", "testament", "pivotal".
  No em-dash overuse, no rule-of-three, no promotional language, no vague attributions.
  Write like a sharp analyst talking to a peer, not a press release.
```

**Scanner 1 — AI Labs & Tooling** (sonnet)
Tiers: 1 (AI Lab & Model Provider Blogs) + 2 (AI Tooling & IDE Companies)

**Scanner 2 — Engineering Blogs & Communities** (haiku)
Tiers: 3 (Tech Company Engineering Blogs) + 4 (Aggregators & Communities)
Focus on: AI/ML adoption, developer tools, infrastructure, agent patterns

**Scanner 3 — Research Papers & Individuals** (sonnet)
Tiers: 5 (Research & Papers) + 6 (Notable Individuals)
Also include newsletters from Tier 4 that are individual/research-focused (Import AI, The Batch, Marvelous MLOps, The Machine Learning Engineer)

**Scanner 4 — YouTube, Podcasts & Market Intel** (haiku)
Tiers: 7 (YouTube & Podcasts) + 8 (Financial & Market Intel)
For each item, also return: `"format": "video|podcast|article"`
For YouTube/podcast pages that need JS rendering, use the Playwright skill to navigate
and extract content. Run: `cd .claude/skills/playwright-skill && node run.js /tmp/scrape-*.js`

**Scanner 5 — MLOps & ML Systems Engineering** (haiku)
Tier: 3b (MLOps & ML Systems Engineering)
Focus on: MLOps, ML infrastructure, model serving, feature stores, ML observability, distributed training, LLMOps

### Step 2: Collect, deduplicate, and batch

Merge all scanner results into a single JSON array. Remove duplicates (same story
from multiple sources — keep the primary source). If a scanner returned zero results,
note it but continue.

If there are many items, use `sweep.py batch` to split for parallel scoring:
```bash
echo '$MERGED_JSON' | python3 sweep.py batch
```

### Step 3: Score each item (sonnet subagent)

Launch scoring subagent(s) — one per batch if batched. Each scorer receives a JSON
array and must return a JSON array with `scores` and `category` added to each item:

```
For each item, assign scores (1-5 each):
- R (Relevance): Directly useful to a senior SWE building with AI/agents?
- Q (Quality): Credible source, data-backed, well-argued?
- N (Novelty): Genuinely new insight vs. rehash?
- A (Actionability): Reader can apply this within a week?
- S (Signal/Noise): High info density, no fluff?

Also assign:
- category: one of [AI Labs & Models, Developer Tools & IDEs, Engineering & Infrastructure, Research Papers, MLOps & ML Systems, Agents & Frameworks, Video & Audio, Market & Funding]
- tldr: 1-2 sentence summary (for items you'd score >= 3.5)

Return as JSON array. Each item must have: all original fields + {"scores": {"R": N, "Q": N, "N": N, "A": N, "S": N}, "category": "...", "tldr": "..."}

Be ruthless. Most items should score below 3.5. Reserve 4.5+ for genuinely exceptional content.
```

### Step 4: Compute scores, filter, and format

Run the deterministic pipeline on the scored JSON:
```bash
echo '$SCORED_JSON' | python3 sweep.py score | python3 sweep.py dedup --seen-file /tmp/seen.json > /tmp/passed.json
```

This calculates weighted averages, assigns PASS/FAIL/MUST READ verdicts, and removes
previously seen URLs.

### Step 5: Check language preference

Read `.claude/lang.conf` in the repo root. If it contains `ko`, all prose content in the
digest must be written in Korean following the korean-translator skill conventions:

- TL;DR summaries for each item -> Korean
- Key Takeaway lines -> Korean
- State of the World section -> Korean
- Top 3 Action Items -> Korean

Keep in English: section headings, score labels, metadata fields, URLs, author names,
stats footer. When writing Korean prose, use 합니다체 register, keep product names in
English, transliterate common technical terms (파이프라인, 에이전트, 모델), translate
abstract concepts (중복 제거, 채점, 가중 평균). See `.claude/skills/korean-translator/SKILL.md`
for the full style guide.

If `lang.conf` is missing or contains `en`, write everything in English.

### Step 6: Generate "State of the World" and "Action Items"

Review the passed items in `/tmp/passed.json` and write:
- **State of the World:** 3-5 sentence synthesis of dominant themes
- **Top 3 Action Items:** Concrete, ranked by urgency and impact

Write in the language determined in Step 5.

**WRITING STYLE (MANDATORY):** Apply humanizer rules from CLAUDE.md. Write like a sharp
analyst talking to a peer. No AI vocabulary, no promotional language, no generic conclusions.
Vary sentence length. Be direct. Use specific numbers. Have opinions. If the writing sounds
like it could have come from a press release, rewrite it.

### Step 7: Format and save

```bash
cat /tmp/passed.json | python3 sweep.py format --scanned $TOTAL --date $(date +%Y-%m-%d) --state-of-world "$STATE" --action-items "$ACTIONS" | python3 sweep.py save
```

Or use the `pipeline` subcommand for Steps 4+6 combined:
```bash
echo '$SCORED_JSON' | python3 sweep.py pipeline --scanned $TOTAL
```

Print the final summary to the user: must-read count, top 3 action items, and file path.
