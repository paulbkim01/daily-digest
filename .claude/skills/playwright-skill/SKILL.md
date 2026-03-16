---
name: playwright-skill
description: Complete browser automation with Playwright. Auto-detects dev servers, writes clean test scripts to /tmp. Test pages, fill forms, take screenshots, check responsive design, validate UX, test login flows, check links, automate any browser task. Use when user wants to test websites, automate browser interactions, validate web functionality, or perform any browser-based testing.
---

**IMPORTANT - Path Resolution:**
This skill can be installed in different locations. Before executing any commands, determine the skill directory based on where you loaded this SKILL.md file, and use that path in all commands below. Replace `$SKILL_DIR` with the actual discovered path.

Common installation paths:

- Plugin system: `~/.claude/plugins/marketplaces/playwright-skill/skills/playwright-skill`
- Manual global: `~/.claude/skills/playwright-skill`
- Project-specific: `<project>/.claude/skills/playwright-skill`

# Playwright Browser Automation

General-purpose browser automation skill. Writes custom Playwright code for any automation task and executes it via the universal executor.

**CRITICAL WORKFLOW - Follow these steps in order:**

1. **Auto-detect dev servers** - For localhost testing, ALWAYS run server detection FIRST:

   ```bash
   cd $SKILL_DIR && node -e "require('./lib/helpers').detectDevServers().then(servers => console.log(JSON.stringify(servers)))"
   ```

   - If **1 server found**: Use it automatically, inform user
   - If **multiple servers found**: Ask user which one to test
   - If **no servers found**: Ask for URL or offer to help start dev server

2. **Write scripts to /tmp** - NEVER write test files to skill directory; always use `/tmp/playwright-test-*.js`

3. **Use visible browser by default** - Always use `headless: false` unless user specifically requests headless mode

4. **Parameterize URLs** - Always make URLs configurable via constant at top of script

## Setup (First Time)

```bash
cd $SKILL_DIR
npm run setup
```

This installs Playwright and Chromium browser. Only needed once.

## Execution Pattern

**Step 1: Detect dev servers (for localhost testing)**

```bash
cd $SKILL_DIR && node -e "require('./lib/helpers').detectDevServers().then(s => console.log(JSON.stringify(s)))"
```

**Step 2: Write test script to /tmp with URL parameter**

```javascript
// /tmp/playwright-test-page.js
const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:3001'; // Auto-detected or from user

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto(TARGET_URL);
  console.log('Page loaded:', await page.title());

  await page.screenshot({ path: '/tmp/screenshot.png', fullPage: true });
  console.log('Screenshot saved to /tmp/screenshot.png');

  await browser.close();
})();
```

**Step 3: Execute from skill directory**

```bash
cd $SKILL_DIR && node run.js /tmp/playwright-test-page.js
```

## Inline Execution (Simple Tasks)

For quick one-off tasks, execute code inline without creating files:

```bash
cd $SKILL_DIR && node run.js "
const browser = await chromium.launch({ headless: false });
const page = await browser.newPage();
await page.goto('http://localhost:3001');
await page.screenshot({ path: '/tmp/quick-screenshot.png', fullPage: true });
console.log('Screenshot saved');
await browser.close();
"
```

**Inline**: Quick one-off tasks (screenshot, element check, page title).
**Files**: Complex tests, anything user might want to re-run.

## Available Helpers

Optional utility functions in `lib/helpers.js`:

```javascript
const helpers = require('./lib/helpers');

const servers = await helpers.detectDevServers();
await helpers.safeClick(page, 'button.submit', { retries: 3 });
await helpers.safeType(page, '#username', 'testuser');
await helpers.takeScreenshot(page, 'test-result');
await helpers.handleCookieBanner(page);
const data = await helpers.extractTableData(page, 'table.results');
```

See `lib/helpers.js` for full list.

## Custom HTTP Headers

Configure custom headers via environment variables:

**Single header:**

```bash
cd $SKILL_DIR && PW_HEADER_NAME=X-Automated-By PW_HEADER_VALUE=playwright-skill node run.js /tmp/my-script.js
```

**Multiple headers (JSON):**

```bash
cd $SKILL_DIR && PW_EXTRA_HEADERS='{"X-Automated-By":"playwright-skill","X-Debug":"true"}' node run.js /tmp/my-script.js
```

Headers are automatically applied when using `helpers.createContext()`:

```javascript
const context = await helpers.createContext(browser);
const page = await context.newPage();
// All requests from this page include your custom headers
```

## Advanced Usage

For comprehensive Playwright API documentation, see [API_REFERENCE.md](API_REFERENCE.md).

## Tips

- **Detect servers FIRST** - Always run `detectDevServers()` before localhost testing
- **Custom headers** - Use `PW_HEADER_NAME`/`PW_HEADER_VALUE` env vars for automated traffic
- **Use /tmp for test files** - Write to `/tmp/playwright-test-*.js`, never to skill directory
- **Parameterize URLs** - Put URL in a `TARGET_URL` constant at the top of every script
- **Visible browser by default** - `headless: false` unless user requests headless
- **Wait strategies** - Use `waitForURL`, `waitForSelector`, `waitForLoadState` instead of fixed timeouts
- **Error handling** - Always use try-catch for robust automation

## Troubleshooting

**Playwright not installed:** `cd $SKILL_DIR && npm run setup`

**Module not found:** Ensure running from skill directory via `run.js` wrapper

**Browser doesn't open:** Check `headless: false` and ensure display available

**Element not found:** Add wait: `await page.waitForSelector('.element', { timeout: 10000 })`
