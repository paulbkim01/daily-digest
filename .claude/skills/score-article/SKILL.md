---
name: score-article
version: 1.0.0
description: |
  Score a single article, paper, video, or podcast against the research quality rubric
  (Relevance, Quality, Novelty, Actionability, Signal/Noise). Fetches content, analyzes it,
  and returns a structured verdict (MUST READ / PASS / FAIL) with justifications. Use this
  skill when the user shares a URL and wants to know if it's worth reading, says things like
  "score this", "is this any good?", "rate this article", "should I read this?", "evaluate
  this paper", or pastes a link and asks for your take on it.
---

# Score Article

Score a single article, paper, video, or podcast against the research quality rubric.

## Instructions

You will be given a URL or description of content to evaluate.

### Step 1: Fetch the content

Use WebFetch to retrieve the content at the given URL. If it's a YouTube video,
search for its transcript or summary. If WebFetch fails (JS-heavy page), use the
Playwright skill to navigate and extract content. If the content is paywalled,
note that and score based on available metadata only.

### Step 2: Analyze and score

Read the scoring rubric from `research-sweep-prompt.md` (Scoring Rubric section).
Apply each criterion scored 1-5. Quick reference:

| Criterion        | Weight | 1 (Low) | 5 (High) |
|------------------|--------|---------|----------|
| **Relevance**    | 1.5x   | Tangential to SWE/AI | Directly applicable to AI-native SWE work |
| **Quality**      | 1.0x   | Opinion, no data | Data-backed, authoritative source |
| **Novelty**      | 1.5x   | Common knowledge rehash | Genuinely new technique or finding |
| **Actionability**| 1.0x   | Pure theory/speculation | Can apply this week with clear steps |
| **Signal/Noise** | 1.0x   | Mostly filler/marketing | Dense, every paragraph adds value |

### Step 3: Calculate weighted score

```
Weighted = (Relevance*1.5 + Quality*1.0 + Novelty*1.5 + Actionability*1.0 + Signal*1.0) / 6.0
```

Or use sweep.py:
```bash
echo '[{"title":"...","url":"...","scores":{"R":X,"Q":X,"N":X,"A":X,"S":X}}]' | python3 sweep.py score
```

### Step 4: Output verdict

```markdown
## Score: [Title]
- **Source:** [URL]
- **Author:** [name] | **Published:** [date] | **Format:** [article/paper/video/podcast]
- **Relevance:** X/5 — [one-line justification]
- **Quality:** X/5 — [one-line justification]
- **Novelty:** X/5 — [one-line justification]
- **Actionability:** X/5 — [one-line justification]
- **Signal/Noise:** X/5 — [one-line justification]
- **Weighted Score:** X.X / 5.0
- **Verdict:** MUST READ (>=4.5) | PASS (>=3.5) | FAIL (<3.5)
- **TL;DR:** 2-3 sentences
- **Key Takeaway:** One actionable insight (if PASS or above)
```

Be honest and rigorous. Most content should score below 3.5. Reserve 4.5+ for
genuinely exceptional content that changes how you think or work.

Write the TL;DR and Key Takeaway in natural, human voice — no AI-isms.
