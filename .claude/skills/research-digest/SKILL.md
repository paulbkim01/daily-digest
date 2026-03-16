---
name: research-digest
version: 1.1.0
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

### Step 1: Check language preference

Read `.claude/lang.conf` in the repo root. If it contains `ko`, all prose content
must be written in Korean. Apply the korean-translator skill
(`.claude/skills/korean-translator/SKILL.md`) for style conventions. Keep section
headings, score labels, metadata, and URLs in English. If `lang.conf` is missing
or contains `en`, write in English.

### Step 2: Filter and organize

- Only include items with weighted score >= 3.5 (thresholds defined in `sweep.py`)
- Group into categories defined in `sweep.py` CATEGORIES list
- MUST READ (>= 4.5) always shown first, then the 8 category sections

### Step 3: Write the digest

For each passing item:

```markdown
### [MUST READ] Title
- **Source:** URL | Author
- **Published:** date | **Format:** type
- **Score:** R:X Q:X N:X A:X S:X -> **Weighted: X.X**
- **TL;DR:** summary
- **Key Takeaway:** actionable insight
```

### Step 4: Synthesize

Write these sections:

**State of the World** (3-5 sentences)
- What are the dominant themes this sweep?
- What shifted since last time?
- What's emerging that people aren't talking about yet?
- What should the reader watch closely?

**Top 3 Action Items**
- Ranked by urgency and impact
- Each should be concrete: "Try X", "Read Y", "Evaluate Z for your project"

**WRITING STYLE:** Apply humanizer rules from `.claude/skills/humanizer/SKILL.md`.
No AI vocabulary, no promotional language. Write like a sharp analyst talking to a peer.

### Step 5: Stats footer

```
Items scanned: X | Passed: Y | Must-reads: Z
Generated: YYYY-MM-DD HH:MM UTC
```

### Step 6: Save

Use sweep.py to save:
```bash
python3 sweep.py save --date $(date +%Y-%m-%d)
```

If a digest already exists for today, sweep.py handles collision detection automatically.
