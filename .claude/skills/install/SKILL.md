---
name: install
version: 1.0.0
description: |
  Set up the research sweep pipeline from scratch. Checks Python 3, Node.js, Playwright,
  Humanizer skill, sweep.py, source registry, and all other skills. Installs missing
  dependencies and runs smoke tests. Use this skill when the user says "set up the project",
  "install everything", "first time setup", "check my environment", "is everything installed?",
  or wants to verify the pipeline is ready to run.
---

# Install & Setup Research Sweep Pipeline

Set up the research sweep pipeline from scratch, verify all dependencies, and run a quick smoke test.

## Instructions

Follow these steps in order. Report status after each step.

### Step 1: Ask the user for their language preference

Before running anything, ask the user:

> Would you like your digests in English or Korean? (English / 한국어)

- If they choose Korean, run: `echo 'ko' > .claude/lang.conf`
- If they choose English (or no preference), run: `echo 'en' > .claude/lang.conf`
- If `.claude/lang.conf` already exists and the user doesn't want to change it, skip this step.

### Step 2: Run the setup script

```bash
bash setup.sh
```

Read the output carefully. If there are errors, fix them before continuing.

### Step 3: Fix any missing dependencies

**If Python 3 is missing:**
```bash
brew install python3
```

**If Node.js is missing:**
```bash
brew install node
```

**If ripgrep (rg) is missing:**
```bash
brew install ripgrep
```

**If Playwright skill needs installing:**
```bash
cd .claude/skills/playwright-skill && npm run setup
```

**If Humanizer skill is missing:**
```bash
cd .claude/skills && git clone https://github.com/blader/humanizer.git
```

Re-run `bash setup.sh` after fixes to confirm everything passes.

### Step 4: Smoke test — verify sweep.py works

```bash
echo '[{"title":"Test","url":"https://example.com","scores":{"R":4,"Q":4,"N":4,"A":4,"S":4}}]' | python3 sweep.py score
```

Expected: JSON output with `weighted` and `verdict` fields added.

### Step 5: Smoke test — verify Playwright works

```bash
cd .claude/skills/playwright-skill && node run.js "
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto('https://example.com');
console.log('Title:', await page.title());
await browser.close();
"
```

Expected: prints "Title: Example Domain"

### Step 6: Report status

Print a summary:

```
Research Sweep Pipeline — Status
================================
Python 3:    [version]
Node.js:     [version]
sweep.py:    [OK/FAIL]
Playwright:  [OK/FAIL]
Humanizer:   [OK/FAIL]
Sources:     [count] sources in registry
Digests:     [count] existing digests
Skills:      research-sweep, scan-sources, score-article, research-digest, install

Ready to run: tell Claude "run a research sweep" or "scan AI labs"
```

If everything passed, tell the user the pipeline is ready.
If anything failed, list exactly what to fix.
