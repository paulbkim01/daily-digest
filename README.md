# Research Sweep Pipeline

[한국어](README.ko.md)

There are too many AI/ML blogs, papers, and YouTube channels to keep up with. This project does it for you. It scans 90+ sources, scores each article on a 5-axis rubric, throws out anything below a 3.5/5.0, and saves what's left as a markdown digest. Built for engineers who'd rather build than read RSS feeds all morning.

## What it does

You tell Claude "run a research sweep" and it:

1. Fans out 15 parallel scanner agents across 8 tiers of sources (AI labs, tooling companies, engineering blogs, MLOps, communities, research papers, YouTube/podcasts, market intel)
2. Collects raw results and deduplicates against the previous digest
3. Scores each item on Relevance, Quality, Novelty, Actionability, and Signal/Noise (weighted average, threshold 3.5/5.0)
4. Filters, groups by category, and formats a markdown digest
5. Writes a "State of the World" synthesis and top 3 action items
6. Saves to `digests/` with automatic date-based naming and collision detection

You get a curated newsletter, not an RSS dump.

## Prerequisites

- Python 3.8+
- Node.js 18+ (for Playwright browser scraping)
- [Claude Code CLI](https://claude.ai/claude-code) installed and authenticated

## Quick start

```bash
# Clone and enter the repo
git clone <repo-url> && cd intel

# Run the setup script (checks deps, installs Playwright, validates everything)
bash setup.sh

# Or let Claude handle setup for you
claude "set up the pipeline"
```

Setup asks you to pick a language (English or Korean) for digest summaries, then checks Python 3, Node.js, sweep.py subcommands, Playwright, the humanizer skill, and the source registry. If anything is missing it tells you exactly what to install.

To switch digest language later without re-running setup:

```bash
echo 'ko' > .claude/lang.conf   # Korean digests
echo 'en' > .claude/lang.conf   # English digests (default)
```

## Usage

Everything runs through natural language in Claude Code. No commands to memorize, just say what you want.

### Full sweep (the main thing)

```bash
claude "run a research sweep"
# or: "what happened this week in AI"
# or: "scan all sources and make a digest"
```

This takes a few minutes. Claude launches 15 scanner agents in parallel (two waves), scores results, and saves a digest to `digests/YYYY-MM-DD.md`.

### Scan a single source tier

```bash
claude "scan AI labs"
claude "check what's new on engineering blogs"
claude "any new ML papers?"
claude "check HN and Reddit"
```

Tiers you can scan individually: `ai-labs`, `tooling`, `eng-blogs`, `mlops`, `communities`, `papers`, `individuals`, `media`, `market`.

### Score a single article

```bash
claude "score this: https://example.com/some-article"
claude "is this paper worth reading? https://arxiv.org/abs/2501.12948"
```

You get scores on all 5 dimensions and a MUST READ / PASS / FAIL verdict.

### Generate a digest from already-scored items

```bash
claude "generate the digest"
claude "format the results into a report"
claude "/loop generate the digest every day"
```

## How scoring works

Each article gets rated 1-5 on five axes (weights and thresholds defined in `sweep.py`):

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| Relevance | 1.5x | Directly useful to a senior SWE building with AI/agents? |
| Quality | 1.0x | Credible source, data-backed, well-argued? |
| Novelty | 1.5x | Genuinely new insight, not a rehash? |
| Actionability | 1.0x | Can you apply this within a week? |
| Signal/Noise | 1.0x | Dense information, no fluff? |

**Weighted average** = (R x 1.5 + Q x 1.0 + N x 1.5 + A x 1.0 + S x 1.0) / 6.0

- **FAIL** (< 3.5): filtered out
- **PASS** (>= 3.5): included in the digest
- **MUST READ** (>= 4.5): promoted to the top section

Most content scores below 3.5. That's the point. You only see what's worth your time.

## Source registry

94 sources organized into 8 tiers:

| Tier | Sources | Examples |
|------|---------|---------|
| 1. AI Labs | 8 | Anthropic, OpenAI, DeepMind, Meta AI, Mistral |
| 2. AI Tooling | 8 | Cursor, Windsurf/Codeium, Vercel, GitHub, LangChain, Hugging Face |
| 3. Engineering Blogs | 15 | Netflix, Stripe, Cloudflare, Shopify, AWS |
| 3b. MLOps | 14 | Weights & Biases, Databricks, Modal, Arize AI |
| 4. Communities | 15 | Hacker News, Reddit (5 subs), dev.to, Lobsters, GitHub Trending, newsletters |
| 5. Research | 6 | arXiv (cs.AI, cs.CL, cs.SE), Hugging Face Papers, Papers With Code |
| 6. Individuals | 14 | Simon Willison, Andrej Karpathy, Chip Huyen |
| 7. Video & Audio | 10 | Lex Fridman, Latent Space, Fireship, Yannic Kilcher |
| 8. Market Intel | 4 | a16z, TechCrunch AI, CB Insights |

60 of these sources have RSS/Atom feeds (fetched by `feed_parser.py`); the remaining 34 use WebSearch fallback.

To add or remove sources, edit both `research-sweep-prompt.md` (source registry) and `feeds.json` (feed URLs). The skills read both at runtime.

## Project structure

```
intel/
  sweep.py                    # Deterministic pipeline (scoring math, dedup, formatting, file I/O)
  feed_parser.py              # RSS/Atom feed fetcher (stdlib-only, no dependencies)
  feeds.json                  # Feed URL registry for all 94 sources
  input.py                    # Interactive config (timeframe, max articles, timeout)
  research-sweep-prompt.md    # Source registry + scoring rubric + rules
  setup.sh                    # Environment setup and validation
  digests/                    # Output directory for markdown digests
  .claude/
    lang.conf                 # Language preference (en or ko)
    skills/
      research-sweep/         # Full sweep orchestrator (15 parallel scanners)
      scan-sources/           # Single-tier scanner
      score-article/          # Individual article scorer
      research-digest/        # Digest formatter
      install/                # Setup and validation
      humanizer/              # AI writing pattern removal
      korean-translator/      # English → Korean technical translation
      playwright-skill/       # Browser automation for JS-heavy sites
```

### Why it's built this way

The split between `sweep.py` and the LLM agents is intentional. Python handles everything deterministic (score math, dedup, formatting, file I/O) while the LLM agents handle everything that needs judgment (searching, scoring 1-5, writing summaries). This way the scoring formula never drifts between runs.

The 15 scanner agents run in two parallel waves. Five high-judgment scanners (AI labs frontier, tooling IDEs, research papers, individual LLM bloggers, media/market) use Sonnet for accuracy. The other ten use Haiku for speed.

Every URL must point to a specific article, not a blog index or homepage. Bad URLs get discarded. This matters because LLMs love to hallucinate plausible-sounding links to blog index pages instead of actual articles.

All writing in the digest goes through a humanizer check that bans words like "delve" and "paradigm", plus patterns like em-dash overuse and negative parallelisms. If someone reads the digest, they shouldn't be able to tell an AI wrote the summaries.

## sweep.py reference

The CLI tool that handles all deterministic operations. Every subcommand reads JSON from stdin and writes to stdout.

```bash
# Extract seen URLs from the most recent digest (for deduplication)
python3 sweep.py seen --digests-dir digests/

# Calculate weighted scores and assign verdicts
echo '$JSON' | python3 sweep.py score

# Remove previously-seen URLs and failed items
echo '$JSON' | python3 sweep.py dedup --seen-file /tmp/seen.json

# Split large item lists into scoring batches
echo '$JSON' | python3 sweep.py batch

# Generate markdown digest from scored items
echo '$JSON' | python3 sweep.py format --date 2026-03-16 --scanned 200

# Save markdown to file with collision detection
echo '$MARKDOWN' | python3 sweep.py save --digests-dir digests/

# Full pipeline: score + dedup + format + save in one step
echo '$JSON' | python3 sweep.py pipeline --digests-dir digests/ --scanned 200
```

## Digest output format

Each digest is a markdown file in `digests/` named by date (`2026-03-16.md`). If you run multiple sweeps in a day, files get suffixed (`2026-03-16-2.md`, `2026-03-16-3.md`).

Sections in order:
1. MUST READ (score >= 4.5), the stuff you should actually stop and read
2. Category sections (AI Labs, Dev Tools, Engineering, Research, MLOps, Agents, Video, Market)
3. State of the World, a 3-5 sentence synthesis of the week's biggest signals
4. Top 3 Action Items, concrete things to try or evaluate
5. Stats footer with scan counts and timestamp

## Adding sources

Edit `research-sweep-prompt.md` and add your source to the appropriate tier section. Format:

```markdown
### Tier N: Category Name
- Source Name (domain.com/path) -- what they cover
```

The scanner agents read this file at runtime, so changes take effect on the next sweep. No code changes needed.

## Troubleshooting

If the setup script reports errors, run `bash setup.sh` and follow its fix instructions. Usually it's a missing Python 3 or Node.js.

If Playwright can't load JS-heavy sites, reinstall the browsers: `cd .claude/skills/playwright-skill && npm run setup`

If the digest has generic blog URLs instead of article links, that's a known LLM failure mode. The pipeline discards items with non-specific URLs, but some slip through. The scanner prompts get better over time.

If the same articles keep showing up across sweeps, the dedup system might not be finding the previous digest. Check that `digests/` has a recent `.md` file.

## License

Private project. Not for redistribution.
