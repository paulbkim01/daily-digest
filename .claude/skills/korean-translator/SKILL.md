---
name: korean-translator
version: 1.0.0
description: |
  Translate English technical writing into natural, professional Korean following the
  style conventions of Kakao Tech and Naver D2 engineering blogs. Handles code docs,
  READMEs, blog posts, and technical articles. Knows which terms to keep in English,
  which to transliterate, and which to translate into native Korean. Use when the user
  asks to "translate to Korean", "write this in Korean", "Korean version", or provides
  English text and asks for a Korean translation.
---

# Korean technical translator

Translate English technical writing into professional Korean that reads like it was
written by a senior Korean engineer for the Kakao Tech or Naver D2 blog. Not a
word-for-word translation, but a natural rewrite in Korean.

## Style guide

This guide is based on analysis of Kakao Tech (tech.kakao.com), Naver D2 (d2.naver.com),
Woowahan Bros tech blog, and Korean open-source README conventions.

### Register: pick one, stay consistent

Use **합니다체** for body text. This is the standard register for Korean technical
documentation, blog posts, and READMEs. Sentence endings: ~합니다, ~됩니다, ~있습니다.

Use **다체** for headings, bullet points, table cells, and footnotes. Sentence endings:
~이다, ~한다, ~된다. This gives headings a noun-phrase quality.

Never mix 합니다체 and 해요체 in the same document. For imperative instructions (setup
steps), use ~합니다 or ~하세요 form.

### What stays in English

Keep these in Roman letters, embedded in Korean sentences:

- **Product and tool names:** Claude Code, Playwright, Python, Node.js, Sonnet, Haiku,
  React, TypeScript, Kubernetes, Docker
- **Library and framework names:** transformers, LangChain, Hugging Face, sweep.py
- **Protocol and standard names:** OAuth2, JWT, HTTP, JSON, API
- **Code identifiers:** function names, class names, variable names, CLI commands,
  file paths, code blocks
- **Abbreviations that are more recognizable in English:** API, DB, LLM, CLI, URL, RSS,
  MLOps, SWE, I/O

### What gets transliterated (Korean phonetic rendering)

Common technical concepts get Korean phonetic spelling:

| English | Korean | Notes |
|---------|--------|-------|
| pipeline | 파이프라인 | |
| scanner | 스캐너 | |
| digest | 다이제스트 | |
| script | 스크립트 | |
| project | 프로젝트 | |
| model | 모델 | |
| prompt | 프롬프트 | |
| cluster | 클러스터 | |
| prototype | 프로토타입 | |
| frontend / backend | 프론트엔드 / 백엔드 | |
| library | 라이브러리 | |
| refactoring | 리팩토링 | |
| dataset | 데이터셋 | |
| hallucination | 할루시네이션 | |
| newsletter | 뉴스레터 | |
| tier | 티어 | |
| formatting | 포맷팅 | |
| skill | 스킬 | |
| agent | 에이전트 | |
| scoring | 채점 (native Korean preferred) | |
| open source | 오픈소스 | |
| fine-tuning | 파인튜닝 | |
| load balancer | 로드밸런서 | |
| tokenizer | 토크나이저 | |
| vibe coding | 바이브 코딩 | |

### What gets translated into native Korean

Abstract concepts should use Sino-Korean or native Korean words:

| English | Korean |
|---------|--------|
| installation | 설치 |
| usage | 사용법 / 사용 방법 |
| architecture / structure | 구조 |
| configuration / settings | 설정 |
| prerequisites / requirements | 사전 요구사항 |
| troubleshooting | 문제 해결 |
| overview / introduction | 개요 / 소개 |
| quick start | 빠른 시작 |
| contributing | 기여 / 기여방법 |
| license | 라이선스 (transliterated) |
| examples | 예제 |
| changelog | 변경 이력 |
| features | 주요 기능 |
| dependency | 의존성 |
| inference | 추론 |
| deduplication | 중복 제거 |
| weighted average | 가중 평균 |
| threshold | 임계값 |
| validation | 검증 / 정합성 검사 |
| consistency check | 정합성 검사 |

### First-mention pattern

On first mention of a potentially unfamiliar term, use the parenthetical pattern:

- 가중 평균(Weighted Average)
- 변경 데이터 캡처(CDC)
- 최소 기능 제품(MVP)

After the first mention, use whichever form is shorter or more natural.

### Heading conventions

Headings should be short Korean noun phrases:

| English heading | Korean heading |
|----------------|----------------|
| What it does | 동작 방식 |
| How scoring works | 채점 방식 |
| Project structure | 프로젝트 구조 |
| Design decisions / Why it's built this way | 설계 의도 |
| Adding sources | 소스 추가 |
| Troubleshooting | 문제 해결 |
| Digest output format | 다이제스트 출력 형식 |
| Quick start | 빠른 시작 |
| Prerequisites | 사전 요구사항 |
| Full sweep (the main thing) | 전체 스윕 (주요 기능) |
| Score a single article | 단일 아티클 채점 |

Avoid sentence-form headings. "프로젝트 구조" is correct. "프로젝트의 구조를 알아봅시다"
is not.

### Sentence patterns

**Opening a section:**
- "이 글에서는 ~에 대해 소개합니다."
- "~에 대해 상세히 설명합니다."

**Explaining purpose:**
- "~의 신뢰성을 보장하기 위해 ~합니다."
- "~를 위해 ~를 구축했습니다."

**Describing behavior:**
- "~에 따라 ~가 자동으로 매핑됩니다."
- "~를 사용하여 ~를 수행합니다."

**Instructions (setup docs):**
- "~를 실행합니다." / "~하려면 다음 명령어를 실행하세요."
- "먼저 ~를 확인합니다."

**Closing:**
- "다음 스윕부터 바로 반영됩니다."
- No sycophantic closings ("감사합니다!" at the end of every section).

### Structural conventions

- Short paragraphs: 2-4 sentences. Single-sentence paragraphs for emphasis.
- Code blocks stay in English with English comments (unless the original has Korean comments).
- Inline code uses backticks: `sweep.py`, `--digests-dir`
- Tables: column headers in Korean, cell content mixes Korean and English freely.

## Instructions

1. Read the source English text.
2. Identify the document type (README, blog post, docs, article).
3. Apply the style guide above to translate section by section.
4. Keep all code blocks, CLI commands, file paths, and product names in English.
5. Use the first-mention parenthetical pattern for technical terms that may be unfamiliar.
6. Match the tone of the original. If the English is casual, the Korean should be
   approachable 합니다체, not stiff academic 다체.
7. After translating, do a pass for:
   - Consistent register (no 합니다체/해요체 mixing)
   - Terms that should have stayed in English but got translated
   - Korean-specific naturalness (does it read like a Kakao Tech post?)
8. Output the translated text.

## Anti-patterns

- Do not over-translate established English terms. Nobody writes "클로드 코드" for Claude Code.
- Do not use 존댓말 (ultra-formal/archaic Korean) in technical docs.
- Do not translate code identifiers, function names, or CLI commands.
- Do not add "(영어)" after every English term.
- Do not write headings as full sentences.
- Do not end every section with "감사합니다" or "도움이 되었기를 바랍니다."
- Do not pad sentences with filler like "~하는 것이 중요합니다" when a direct statement works.
