#!/usr/bin/env bash
set -euo pipefail

# Research Sweep Pipeline — Setup Script
# Installs all dependencies and validates the environment.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$REPO_DIR/.claude/skills"
PW_DIR="$SKILL_DIR/playwright-skill"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "======================================"
echo "  Research Sweep Pipeline — Setup"
echo "======================================"
echo ""

ERRORS=0
LANG_CONF="$REPO_DIR/.claude/lang.conf"

# ── 0. Language selection ─────────────────────────────────────────────────────
echo "--- Language / 언어 선택 ---"
if [ -t 0 ]; then
  echo "  [1] English (default)"
  echo "  [2] 한국어"
  echo ""
  read -r -p "Select language / 언어를 선택하세요 [1/2]: " LANG_CHOICE
else
  # Non-interactive: keep existing setting or default to English
  if [ -f "$LANG_CONF" ]; then
    LANG_CHOICE=""
    DIGEST_LANG="$(cat "$LANG_CONF")"
  else
    LANG_CHOICE="1"
  fi
fi

case "$LANG_CHOICE" in
  2)
    DIGEST_LANG="ko"
    ok "다이제스트 언어: 한국어"
    ;;
  "")
    ok "Keeping existing language: $DIGEST_LANG"
    ;;
  *)
    DIGEST_LANG="en"
    ok "Digest language: English"
    ;;
esac

mkdir -p "$(dirname "$LANG_CONF")"
echo "$DIGEST_LANG" > "$LANG_CONF"
ok "Saved to .claude/lang.conf"
echo ""

# ── 1. Python 3 ──────────────────────────────────────────────────────────────
echo "--- Checking Python 3 ---"
if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1)
  ok "Found $PY_VER"
else
  fail "Python 3 not found. Install it: brew install python3"
  ERRORS=$((ERRORS + 1))
fi

# ── 2. Node.js (for Playwright) ──────────────────────────────────────────────
echo "--- Checking Node.js ---"
if command -v node &>/dev/null; then
  NODE_VER=$(node --version 2>&1)
  ok "Found Node.js $NODE_VER"
else
  fail "Node.js not found. Install it: brew install node"
  ERRORS=$((ERRORS + 1))
fi

# ── 2b. CLI tools (ripgrep, git, diff) ────────────────────────────────────────
echo "--- Checking CLI tools ---"
if command -v rg &>/dev/null; then
  RG_VER=$(rg --version | head -1)
  ok "Found $RG_VER"
else
  warn "ripgrep (rg) not found — installing via brew"
  if command -v brew &>/dev/null; then
    brew install ripgrep
    ok "ripgrep installed"
  else
    fail "ripgrep not found and brew unavailable. Install manually: https://github.com/BurntSushi/ripgrep#installation"
    ERRORS=$((ERRORS + 1))
  fi
fi

if command -v git &>/dev/null; then
  GIT_VER=$(git --version)
  ok "Found $GIT_VER"
else
  fail "git not found. Install it: brew install git"
  ERRORS=$((ERRORS + 1))
fi

if command -v diff &>/dev/null; then
  ok "diff available"
else
  warn "diff not found (usually ships with macOS)"
fi

# ── 3. sweep.py validation ───────────────────────────────────────────────────
echo "--- Checking sweep.py ---"
if [ -f "$REPO_DIR/sweep.py" ]; then
  if python3 -c "import json, re, sys, argparse" 2>/dev/null; then
    ok "sweep.py present, stdlib deps available"
  else
    fail "Python stdlib modules missing"
    ERRORS=$((ERRORS + 1))
  fi
else
  fail "sweep.py not found at $REPO_DIR/sweep.py"
  ERRORS=$((ERRORS + 1))
fi

# ── 4. Playwright skill ─────────────────────────────────────────────────────
echo "--- Setting up Playwright skill ---"
if [ -d "$PW_DIR" ]; then
  if [ -f "$PW_DIR/package.json" ]; then
    if [ -d "$PW_DIR/node_modules/playwright" ]; then
      ok "Playwright already installed"
    else
      echo "  Installing Playwright dependencies..."
      (cd "$PW_DIR" && npm run setup)
      if [ $? -eq 0 ]; then
        ok "Playwright installed successfully"
      else
        fail "Playwright install failed"
        ERRORS=$((ERRORS + 1))
      fi
    fi
  else
    fail "playwright-skill/package.json missing"
    ERRORS=$((ERRORS + 1))
  fi
else
  warn "Playwright skill not found at $PW_DIR"
  echo "  To install: cd .claude/skills && git clone https://github.com/lackeyjb/playwright-skill.git"
  echo "  Then re-run this script."
fi

# ── 5. Humanizer skill ──────────────────────────────────────────────────────
echo "--- Checking Humanizer skill ---"
if [ -f "$SKILL_DIR/humanizer/SKILL.md" ]; then
  ok "Humanizer skill present"
else
  warn "Humanizer skill not found at $SKILL_DIR/humanizer/"
  echo "  The humanizer skill should be at .claude/skills/humanizer/. Re-clone the repository if missing."
fi

# ── 6. Digests directory ─────────────────────────────────────────────────────
echo "--- Checking digests directory ---"
mkdir -p "$REPO_DIR/digests"
ok "digests/ directory ready"

# ── 7. Source registry ───────────────────────────────────────────────────────
echo "--- Checking source registry ---"
if [ -f "$REPO_DIR/research-sweep-prompt.md" ]; then
  SOURCE_COUNT=$(grep -c "^- " "$REPO_DIR/research-sweep-prompt.md" 2>/dev/null || echo "0")
  ok "research-sweep-prompt.md present ($SOURCE_COUNT sources)"
else
  fail "research-sweep-prompt.md not found"
  ERRORS=$((ERRORS + 1))
fi

# ── 8. Claude skills ─────────────────────────────────────────────────────────
echo "--- Checking Claude skills ---"
SKILLS=("research-sweep" "research-digest" "scan-sources" "score-article" "install")
for skill in "${SKILLS[@]}"; do
  if [ -f "$SKILL_DIR/$skill/SKILL.md" ]; then
    ok "  $skill skill present"
  else
    warn "  $skill skill not found"
  fi
done

# ── 9. Verify sweep.py subcommands ──────────────────────────────────────────
echo "--- Verifying sweep.py subcommands ---"
for subcmd in seen score dedup batch format save pipeline; do
  if python3 "$REPO_DIR/sweep.py" "$subcmd" --help &>/dev/null; then
    ok "  sweep.py $subcmd"
  else
    fail "  sweep.py $subcmd failed"
    ERRORS=$((ERRORS + 1))
  fi
done

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "======================================"
if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}  Setup complete. No errors.${NC}"
  echo "  Language: $(cat "$LANG_CONF" 2>/dev/null || echo "en")"
  echo ""
  if [ "$(cat "$LANG_CONF" 2>/dev/null)" = "ko" ]; then
    echo "  빠른 시작:"
    echo "    claude \"run a research sweep\"   # 전체 소스 스윕"
    echo "    claude \"scan AI labs\"            # 단일 티어 스캔"
    echo "    claude \"score this: <url>\"       # 아티클 하나 채점"
    echo ""
    echo "  다이제스트의 요약과 분석이 한국어로 작성됩니다."
    echo "  언어 변경: echo 'en' > .claude/lang.conf"
  else
    echo "  Quick start:"
    echo "    claude \"run a research sweep\"   # Full sweep across all sources"
    echo "    claude \"scan AI labs\"            # Scan a single tier"
    echo "    claude \"score this: <url>\"       # Score one article"
    echo ""
    echo "  To switch to Korean digests: echo 'ko' > .claude/lang.conf"
  fi
else
  echo -e "${RED}  Setup finished with $ERRORS error(s).${NC}"
  echo "  Fix the issues above and re-run: bash setup.sh"
fi
echo "======================================"
