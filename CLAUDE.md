# Research Sweep Pipeline

AI-powered research digest generator. Scans 80+ sources, scores articles, and produces weekly digests for senior SWEs building with AI/agents.

## Setup

First time? Ask Claude to "install the pipeline" or run `bash setup.sh`.

## Architecture

- `sweep.py` — deterministic pipeline (scoring math, dedup, formatting, file I/O)
- `research-sweep-prompt.md` — single source of truth for sources and rubric
- `.claude/skills/` — skills auto-discovered by Claude (pipeline stages, humanizer, playwright)
- `digests/` — output directory for markdown digests

## Skills Integration

### Humanizer (writing quality)

All writing output — tldrs, State of the World, Action Items — must go through a humanizer pass. Apply these rules to any text you write for the digest:

- No AI vocabulary: avoid "delve", "landscape", "paradigm", "leverage", "robust", "comprehensive", "tapestry", "testament", "pivotal", "foster", "underscore", "showcase"
- No em-dash overuse, no rule-of-three patterns, no promotional language
- No negative parallelisms ("It's not just X; it's Y")
- No vague attributions ("Experts say", "Industry observers")
- No generic conclusions ("The future looks bright")
- Write like a sharp analyst talking to a peer in Slack, not a press release
- Vary sentence length. Be direct. Use concrete numbers over abstractions.
- Have opinions. Acknowledge complexity. Let some edge in.

Full reference: `.claude/skills/humanizer/SKILL.md`

### Playwright (browser scraping)

Use Playwright for sources that need JavaScript rendering or page navigation. Especially useful for:

- YouTube/podcast pages (Tier 7) where transcripts need JS
- Blog index pages that load content dynamically
- Sites that block simple fetch but render for real browsers
- Extracting article links from paginated blog archives

Skill dir: `.claude/skills/playwright-skill/`
Setup: `cd .claude/skills/playwright-skill && npm run setup`

When scraping with Playwright, use headless mode and the Accept: text/markdown header where supported:
```bash
PW_HEADER_NAME=Accept PW_HEADER_VALUE=text/markdown cd .claude/skills/playwright-skill && node run.js /tmp/scrape-script.js
```

### Korean translation (digest language)

The pipeline supports Korean digest output. The language preference is stored in `.claude/lang.conf` (`en` or `ko`), set during `bash setup.sh`. When `ko` is selected:

- TL;DR summaries, State of the World, and Action Items are written in Korean
- Section headings, score labels, metadata fields, URLs stay in English
- Uses 합니다체 register, keeps product names in English, transliterates common terms
- Style follows Kakao Tech / Naver D2 blog conventions

To switch languages without re-running setup: `echo 'ko' > .claude/lang.conf` or `echo 'en' > .claude/lang.conf`

Full reference: `.claude/skills/korean-translator/SKILL.md`

## Skills

Claude auto-discovers these skills from `.claude/skills/`. No slash commands needed, just describe what you want.

| Skill | Triggered by |
|-------|-------------|
| install | "set up the pipeline", "install dependencies" |
| research-sweep | "run a full sweep", "scan and score all sources" |
| scan-sources | "scan tier 3", "check a source tier" |
| score-article | "score this article", providing a URL |
| research-digest | "generate the digest", "format the digest" |
| korean-translator | "translate to Korean", "Korean version" |

## Writing Style

All digest content must sound human-written. Before finalizing any digest, mentally ask: "Would I be embarrassed if someone thought an AI wrote this?" If yes, rewrite it.
