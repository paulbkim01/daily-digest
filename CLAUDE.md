# Research Sweep Pipeline

AI-powered research digest generator. Scans 90+ sources, scores articles, and produces weekly digests for senior SWEs building with AI/agents.

## Setup

First time? Ask Claude to "install the pipeline" or run `bash setup.sh`.

## Architecture

- `sweep.py` — deterministic pipeline (scoring math, dedup, formatting, coverage, JSON repair, file I/O)
- `feed_parser.py` — RSS/Atom feed fetcher (stdlib-only, no dependencies)
- `transcriber.py` — audio/video transcription (captions download, yt-dlp audio extraction, OpenRouter API transcription)
- `feeds.json` — feed URL registry for all 102 sources (used by feed_parser.py)
- `input.py` — interactive config (timeframe, max articles, timeout) → writes `/tmp/sweep-config.json`
- `research-sweep-prompt.md` — single source of truth for source registry and rubric prose (scoring math in sweep.py)
- `.claude/skills/` — skills auto-discovered by Claude (pipeline stages, humanizer, playwright)
- `digests/` — output directory for markdown digests

## Skills Integration

### Humanizer (writing quality)

All writing output must go through a humanizer pass. Avoid AI vocabulary ("delve", "landscape",
"paradigm", etc.), em-dash overuse, rule-of-three patterns, and promotional language. Write like
a sharp analyst talking to a peer, not a press release.

Full rules: `.claude/skills/humanizer/SKILL.md`

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
cd .claude/skills/playwright-skill && PW_HEADER_NAME=Accept PW_HEADER_VALUE=text/markdown node run.js /tmp/scrape-script.js
```

### Transcriber (audio/video)

For Tier 7 (YouTube & Podcasts), use `transcriber.py` to get actual content for scoring:

- **Captions first (free):** `python3 transcriber.py captions <url>` — uses YouTube auto-captions
- **Audio fallback (paid):** `python3 transcriber.py pipeline <url>` — downloads audio, transcribes via OpenRouter
- **Search YouTube:** `python3 transcriber.py search "query"` — find relevant videos
- **Dependencies:** `yt-dlp` (pip), `ffmpeg` (brew), `OPENROUTER_API_KEY` (env var, only for paid transcription)

Cost: ~$0.58/hour of audio via `openai/gpt-audio-mini`. YouTube captions are free.

Full reference: `.claude/skills/transcribe-audio/SKILL.md`

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
| humanizer | "humanize this text", reviewing writing quality |
| korean-translator | "translate to Korean", "Korean version" |
| playwright-skill | browser automation, scraping JS-heavy pages |
| transcribe-audio | "transcribe this video", "get the transcript", YouTube/podcast URL |

## Writing Style

All digest content must sound human-written. Before finalizing any digest, mentally ask: "Would I be embarrassed if someone thought an AI wrote this?" If yes, rewrite it.
