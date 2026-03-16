# Research Sweep Pipeline

[English](README.md)

AI/ML 블로그, 논문, YouTube 채널이 너무 많아서 다 읽기 힘들잖아요? 이 프로젝트가 대신 해줍니다. 94개의 소스를 스캔하고, 각 아티클을 5개 축으로 평가한 뒤, 순위를 매겨 가치가 있는 글들의 리스트를 정리합니다. 아침마다 RSS 피드 읽느라 시간 쓰기 싫은 엔지니어를 위해 만들었습니다.

## 동작 방식

Claude에게 "run a research sweep"이라고 말하면 다음과 같이 동작합니다:

1. 8개 티어의 소스(AI 연구소, 툴링 회사, 엔지니어링 블로그, MLOps, 커뮤니티, 논문, YouTube/팟캐스트, 시장 동향)에 15개의 스캐너 에이전트를 병렬로 분산 실행
2. 수집된 결과를 이전 다이제스트와 비교해 중복 제거
3. 각 항목을 Relevance, Quality, Novelty, Actionability, Signal/Noise 기준으로 채점 (가중 평균, 임계값 3.5/5.0)
4. 카테고리별로 분류하고 마크다운 다이제스트로 포맷팅
5. "State of the World" 종합 분석과 상위 3개 액션 아이템 작성
6. `digests/`에 날짜 기반 파일명으로 저장 (충돌 시 자동 번호 부여)

RSS 덤프가 아니라 큐레이션된 뉴스레터를 받게 됩니다.

## 사전 요구사항

- Python 3.8+
- Node.js 18+ (Playwright 브라우저 스크래핑용)
- [Claude Code CLI](https://claude.ai/claude-code) 설치 및 인증 완료

## 빠른 시작

```bash
# 저장소 클론 및 진입
git clone <repo-url> && cd intel

# 셋업 스크립트 실행 (의존성 확인, Playwright 설치, 전체 검증)
bash setup.sh

# 또는 Claude에게 셋업을 맡길 수도 있습니다
claude "set up the pipeline"
```

셋업 스크립트는 다이제스트 언어(English / 한국어)를 먼저 선택하게 한 뒤, Python 3, Node.js, sweep.py 서브커맨드, Playwright, humanizer 스킬, 소스 레지스트리를 확인합니다. 빠진 게 있으면 정확히 뭘 설치해야 하는지 알려줍니다.

셋업 없이 언어를 변경하려면:

```bash
echo 'ko' > .claude/lang.conf   # 한국어 다이제스트
echo 'en' > .claude/lang.conf   # 영어 다이제스트 (기본값)
```

## 사용법

모든 기능은 Claude Code에서 자연어로 실행합니다. 외울 명령어는 없고, 원하는 걸 말하면 됩니다.

### 전체 스윕 (주요 기능)

```bash
claude "run a research sweep"
# 또는: "what happened this week in AI"
# 또는: "scan all sources and make a digest"
```

몇 분 정도 소요됩니다. Claude가 15개의 스캐너 에이전트를 두 차례에 걸쳐 병렬로 띄우고, 결과를 채점한 뒤, `digests/YYYY-MM-DD.md`로 저장합니다.

### 단일 소스 티어 스캔

```bash
claude "scan AI labs"
claude "check what's new on engineering blogs"
claude "any new ML papers?"
claude "check HN and Reddit"
```

개별 스캔 가능한 티어: `ai-labs`, `tooling`, `eng-blogs`, `mlops`, `communities`, `papers`, `individuals`, `media`, `market`

### 단일 아티클 채점

```bash
claude "score this: https://example.com/some-article"
claude "is this paper worth reading? https://arxiv.org/abs/2501.12948"
```

5개 채점 항목의 점수와 MUST READ / PASS / FAIL 판정을 받을 수 있습니다.

### 채점 완료된 항목으로 다이제스트 생성

```bash
claude "full research sweep 시작해줘"
claude "/loop full research sweep 시작해줘 everyday"
```

## 채점 방식

각 아티클은 5개 항목에 대해 1-5점으로 평가됩니다 (가중치와 임계값은 `sweep.py`에 정의):

| 항목 | 가중치 | 평가 기준 |
|------|--------|----------|
| Relevance (관련성) | 1.5x | AI/에이전트를 다루는 시니어 엔지니어에게 직접 도움이 되는가? |
| Quality (품질) | 1.0x | 신뢰할 수 있는 소스인가? 데이터에 기반하고, 논거가 탄탄한가? |
| Novelty (새로움) | 1.5x | 이미 알려진 내용의 반복이 아닌, 진짜 새로운 인사이트인가? |
| Actionability (실행 가능성) | 1.0x | 일주일 안에 적용해볼 수 있는가? |
| Signal/Noise (정보 밀도) | 1.0x | 내용이 밀도 있는가? 군더더기는 없는가? |

**가중 평균** = (R x 1.5 + Q x 1.0 + N x 1.5 + A x 1.0 + S x 1.0) / 6.0

- FAIL (< 3.5): 필터링됨
- PASS (>= 3.5): 목록에 포함
- MUST READ (>= 4.5): 최상단 섹션으로 승격

대부분의 콘텐츠는 3.5 미만으로 떨어집니다. 의도된 설계입니다. 시간 쓸 가치가 있는 것만 보여줍니다.

## 소스 레지스트리

94개의 소스를 8개 티어로 구성했습니다:

| 티어 | 소스 수 | 예시 |
|------|---------|------|
| 1. AI 연구소 | 8 | Anthropic, OpenAI, DeepMind, Meta AI, Mistral |
| 2. AI 툴링 | 8 | Cursor, Windsurf/Codeium, Vercel, GitHub, LangChain, Hugging Face |
| 3. 엔지니어링 블로그 | 15 | Netflix, Stripe, Cloudflare, Shopify, AWS |
| 3b. MLOps | 14 | Weights & Biases, Databricks, Modal, Arize AI |
| 4. 커뮤니티 | 15 | Hacker News, Reddit (5개 서브), dev.to, Lobsters, GitHub Trending, 뉴스레터 |
| 5. 논문 | 6 | arXiv (cs.AI, cs.CL, cs.SE), Hugging Face Papers, Papers With Code |
| 6. 개인 블로그 | 14 | Simon Willison, Andrej Karpathy, Chip Huyen |
| 7. 영상 및 오디오 | 10 | Lex Fridman, Latent Space, Fireship, Yannic Kilcher |
| 8. 시장 동향 | 4 | a16z, TechCrunch AI, CB Insights |

이 중 60개 소스는 RSS/Atom 피드를 지원하고 (`feed_parser.py`로 수집), 나머지 34개는 WebSearch를 사용합니다.

소스를 추가하거나 제거하려면 `research-sweep-prompt.md`(소스 레지스트리)와 `feeds.json`(피드 URL)을 함께 편집하면 됩니다. 스킬들이 런타임에 두 파일 모두 읽어갑니다.

## 프로젝트 구조

```
intel/
  sweep.py                    # 결정론적 파이프라인 (채점 계산, 중복 제거, 포맷팅, 파일 I/O)
  feed_parser.py              # RSS/Atom 피드 수집기 (stdlib 전용, 외부 의존성 없음)
  feeds.json                  # 94개 소스의 피드 URL 레지스트리
  input.py                    # 대화형 설정 (타임프레임, 최대 아티클 수, 타임아웃)
  research-sweep-prompt.md    # 소스 레지스트리 + 채점 기준 + 규칙
  setup.sh                    # 환경 설정 및 검증
  digests/                    # 마크다운 다이제스트 출력 디렉토리
  .claude/
    lang.conf                 # 언어 설정 (en 또는 ko)
    skills/
      research-sweep/         # 전체 스윕 오케스트레이터 (15개 병렬 스캐너)
      scan-sources/           # 단일 티어 스캐너
      score-article/          # 개별 아티클 채점기
      research-digest/        # 다이제스트 포맷터
      install/                # 셋업 및 검증
      humanizer/              # AI 작문 패턴 제거
      korean-translator/      # 영어 → 한국어 기술 번역
      playwright-skill/       # JS 렌더링이 필요한 사이트용 브라우저 자동화
```

### 설계 의도

`sweep.py`와 LLM 에이전트의 역할 분리는 의도적입니다. Python은 결정론적 작업(채점 계산, 중복 제거, 포맷팅, 파일 I/O)을 담당하고, LLM 에이전트는 판단이 필요한 작업(소스 검색, 1-5점 채점, 요약 작성)을 담당합니다. 이렇게 하면 채점 공식이 실행마다 흔들리지 않습니다.

15개 스캐너 에이전트는 두 차례의 웨이브로 병렬 실행됩니다. 판단력이 중요한 5개 스캐너(AI 연구소 선두 그룹, 툴링 IDE, 논문, 개인 LLM 블로거, 미디어/마켓)는 정확도를 위해 Sonnet을 사용하고, 나머지 10개는 속도를 위해 Haiku를 사용합니다.

모든 URL은 특정 아티클을 가리켜야 하고, 블로그 인덱스나 홈페이지 URL은 버립니다. LLM이 블로그 인덱스 페이지를 그럴싸하게 지어내서 링크하는 문제가 잦기 때문입니다.

다이제스트에 포함되는 모든 글은 humanizer 검사를 통과해야 합니다. "delve", "paradigm" 같은 단어와 em dash 남용, 부정 병렬 구문 같은 패턴을 금지합니다. 다이제스트를 읽는 사람이 AI가 쓴 건지 모를 정도가 목표입니다.

## sweep.py 레퍼런스

모든 결정론적 연산을 처리하는 CLI 도구입니다. 모든 서브커맨드는 stdin에서 JSON을 읽고 stdout으로 출력합니다.

```bash
# 가장 최근 다이제스트에서 기존 URL 추출 (중복 제거용)
python3 sweep.py seen --digests-dir digests/

# 가중 점수 계산 및 판정 부여
echo '$JSON' | python3 sweep.py score

# 기존에 본 URL과 FAIL 항목 제거
echo '$JSON' | python3 sweep.py dedup --seen-file /tmp/seen.json

# 항목이 많을 때 채점 배치로 분할
echo '$JSON' | python3 sweep.py batch

# 채점된 항목으로 마크다운 다이제스트 생성
echo '$JSON' | python3 sweep.py format --date 2026-03-16 --scanned 200

# 마크다운을 파일로 저장 (충돌 감지 포함)
echo '$MARKDOWN' | python3 sweep.py save --digests-dir digests/

# 전체 파이프라인: score + dedup + format + save 한 번에 실행
echo '$JSON' | python3 sweep.py pipeline --digests-dir digests/ --scanned 200
```

## 다이제스트 출력 형식

각 다이제스트는 `digests/` 디렉토리에 날짜별 마크다운 파일로 저장됩니다 (`2026-03-16.md`). 하루에 여러 번 스윕을 실행하면 접미사가 붙습니다 (`2026-03-16-2.md`, `2026-03-16-3.md`).

섹션 순서:
1. MUST READ (점수 >= 4.5), 실제로 읽어볼 가치가 있는 항목
2. 카테고리별 섹션 (AI Labs, Dev Tools, Engineering, Research, MLOps, Agents, Video, Market)
3. State of the World, 금주의 주요 시그널을 3-5문장으로 종합
4. Top 3 Action Items, 실제로 해볼 만한 것들
5. 통계 푸터 (스캔 수, 통과 수, 생성 시각)

## 소스 추가

`research-sweep-prompt.md`를 열고, 해당하는 티어 섹션에 소스를 추가하면 됩니다. 형식은 다음과 같습니다:

```markdown
### Tier N: Category Name
- Source Name (domain.com/path) -- 다루는 주제
```

스캐너 에이전트가 런타임에 이 파일을 읽기 때문에, 다음 스윕부터 바로 반영됩니다. 코드 수정은 필요 없습니다.

## 문제 해결

셋업 스크립트에서 에러가 나면 `bash setup.sh`를 실행하고 안내에 따르면 됩니다. 대부분 Python 3이나 Node.js가 없는 경우입니다.

Playwright가 JS 렌더링이 많은 사이트를 로드하지 못하면, 브라우저를 다시 설치합니다: `cd .claude/skills/playwright-skill && npm run setup`

다이제스트에 아티클 링크 대신 블로그 인덱스 URL이 들어가 있다면, 이건 알려진 LLM 문제입니다. 파이프라인이 비특정 URL을 걸러내지만, 간혹 빠져나가는 경우가 있습니다. 스캐너 프롬프트는 계속 개선 중입니다.

같은 아티클이 스윕마다 반복해서 나타난다면, 중복 제거 시스템이 이전 다이제스트를 찾지 못하고 있을 수 있습니다. `digests/` 디렉토리에 최근 `.md` 파일이 있는지 확인해 보세요.

## 라이선스

비공개 프로젝트입니다. 재배포를 금지합니다.
