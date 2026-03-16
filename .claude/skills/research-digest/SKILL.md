---
name: research-digest
version: 1.0.0
description: |
  Generate a polished, publication-quality research digest from scored items. Filters by
  quality threshold, groups into categories, writes human-sounding TL;DRs, synthesizes a
  "State of the World" narrative, and produces top 3 action items. Use this skill whenever
  the user wants to format scored research items into a digest, compile findings into a
  readable report, or says things like "make the digest", "format these results",
  "write up the findings", or "generate the report from scored items".
---

# Research Digest Generator

Generate a polished research digest from scored items. Used as the final step
of the research sweep pipeline, or standalone to compile manually scored items.

## Instructions

You will receive a list of scored research items. Your job is to produce a
publication-quality digest.

### Input format expected

Each item should have: title, URL, author, date, format, scores (R/Q/N/A/S),
weighted score, TL;DR, and key takeaway.

### Step 1: Filter and organize

- Only include items with weighted score >= 3.5
- Group into categories:
  - MUST READ (>= 4.5) — always shown first
  - AI Labs & Models
  - Developer Tools & IDEs
  - Engineering & Infrastructure
  - Research Papers
  - MLOps & ML Systems
  - Agents & Frameworks
  - Video & Audio
  - Market & Funding

### Step 2: Write the digest

For each passing item:

```markdown
### [MUST READ] Title
- **Source:** URL | Author
- **Published:** date | **Format:** type
- **Score:** R:X Q:X N:X A:X S:X -> **Weighted: X.X**
- **TL;DR:** summary
- **Key Takeaway:** actionable insight
```

### Step 3: Synthesize

Write these sections:

**State of the World** (3-5 sentences)
- What are the dominant themes this sweep?
- What shifted since last time?
- What's emerging that people aren't talking about yet?
- What should the reader watch closely?

**Top 3 Action Items**
- Ranked by urgency and impact
- Each should be concrete: "Try X", "Read Y", "Evaluate Z for your project"

**WRITING STYLE (MANDATORY):** Apply humanizer rules from CLAUDE.md to ALL text output.
- No AI vocabulary: "delve", "landscape", "paradigm", "leverage", "robust", "comprehensive", "tapestry", "testament", "pivotal", "foster", "underscore", "showcase"
- No em-dash overuse, no rule-of-three, no promotional language, no vague attributions
- No negative parallelisms ("It's not just X; it's Y"), no generic conclusions
- Write like a sharp analyst talking to a peer in Slack, not a press release
- Vary sentence length. Be direct. Use concrete numbers over abstractions.
- TL;DRs should sound like something a real person would say, not a corporate summary.

### Step 4: Stats footer

```
Items scanned: X | Passed: Y | Must-reads: Z
Generated: YYYY-MM-DD HH:MM UTC
```

### Step 5: Check language preference

Read `.claude/lang.conf` in the repo root. If it contains `ko`, apply the korean-translator
skill to all prose content in the digest:

- TL;DR summaries for each item
- Key Takeaway lines
- State of the World section
- Top 3 Action Items section

Keep structural elements in English: section headings (## MUST READ, ## AI Labs & Models),
score labels (R:X Q:X), metadata fields (Source, Published, Format, Weighted), URLs,
author names, and the stats footer format.

If `lang.conf` is missing or contains `en`, write everything in English as usual.

### Step 6: Save

Use sweep.py to save:
```bash
python3 sweep.py save --date $(date +%Y-%m-%d)
```

If a digest already exists for today, sweep.py handles collision detection automatically.
