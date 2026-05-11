# Context Notes

세션을 이어가는 사람(본인 or Claude)이 결정 배경을 빠르게 파악하기 위한 메모. 새로운 결정마다 append-only로 누적.

---

## 2026-05-10 — 프로젝트 시작 (집 PC, macOS)

### 상황
- 사용자는 해외채권 운용 데스크. 8가지 trading 포지션을 수시 점검 중.
- 매일 아침 7~8시(KST)에 팀이 함께 보는 정량 대시보드가 필요.
- 단순 수치가 아닌 percentile/z-score 등 통계적 위치 정보가 핵심 요구.

### 결정 1 — LSEG MCP 미사용
- LSEG OAuth 인증은 성공했으나 LFA API entitlement 5종 모두 권한 거부.
  - `LFA_API/EP_IRCURVES` (금리 커브)
  - `LFA_API/EP_SWAPS` (스왑)
  - `API_ACCESS_CONTROL/MCP_DATA_QA_ON` (QA 매크로)
  - `API_HIST_PRIC_SUMMARIES_READ` (히스토리컬 가격)
  - `API_ACCESS_CONTROL/MCP_DATA_ON` (물가 커브)
- 회사에서 LSEG 라이선스 추가 신청은 어렵다는 사용자 의견. → LSEG 제외 확정.

### 결정 2 — Daloopa 미사용
- Daloopa는 기업 펀더멘털(매출/EPS/KPI) 영역. 매크로/금리/FX/크레딧 데이터는 다루지 않음.
- 본 프로젝트와 도메인 불일치. → 제외 확정.

### 결정 3 — Bloomberg Terminal API 단일 소스
- 사용자 회사 PC에 Bloomberg Terminal 사용 가능. Python SDK `blpapi` 설치도 가능.
- UST 전 만기, BEI/TIPS, 스왑/스왑스프레드, SOFR 선물, Fed BS 항목, 매크로 지표, 주가지수, FX, BTP/Bund/JGB/Gilt까지 단일 소스로 95%+ 커버 가능.
- 보조 — UST 입찰은 TreasuryDirect (Phase 4에서).

### 결정 4 — Tier 2 정적 사이트 (단일 HTML 아님)
- 단일 자기완결 HTML(Tier 1)은 history 누적 불가, 페이지 분할 불가.
- React/SPA(Tier 3)는 본 용도엔 과한 엔지니어링.
- → Jinja2 + 정적 HTML로 history 폴더 누적 가능한 형태로 결정.

### 결정 5 — 본인 PC HTTP 서버 호스팅
- `python -m http.server 8000` 한 줄로 충분.
- 동료들은 사내 IP로 접속. 사내 web server 따로 운영 안 함.

### 결정 6 — 06:30 KST 자동 갱신
- 미국 NFP/CPI 발표는 한국시간 21:30~23:30. 익일 새벽이면 충분히 반영.
- 평일만 동작 (주말은 데이터 변동 거의 없음).

### 결정 7 — 디바이스 분리 (개발 macOS, 운영 Windows)
- 현재 작업은 macOS (집 PC). 실제 데이터 fetch와 운영은 Windows 10 (회사 PC).
- 제약 — `blpapi`는 Bloomberg Terminal이 있는 회사 PC에서만 실데이터 호출 가능.
- 대응 — `fetch_bloomberg.py`에 `--mode dev`(mock 데이터) / `--mode production`(실데이터) 두 모드 분리.
- 경로 처리는 `pathlib`로 크로스 플랫폼.
- 파일 인코딩 UTF-8 명시 (Windows 콘솔 한글 깨짐 방지).

### 결정 8 — GitHub Private repo로 코드 이동
- 집 PC ↔ 회사 PC 양방향 sync에 가장 적합.
- `data/`, `output/`, `logs/`는 `.gitignore` (실데이터/생성물은 repo 밖).

### 결정 9 — percentile / z-score 기본 윈도우 3Y
- 운용역 감각으로 "최근 사이클 내 위치" 보기 적합.
- 정책금리·실질금리는 5Y 병기 (하나의 사이클이 더 길기 때문).
- Phase 3에서 1Y/5Y 토글 추가 검토.

### 결정 10 — Phase 1은 mock 데이터로 e2e 검증까지
- macOS에서 blpapi 못 돌리니 Phase 1 종료 시점 = "mock 데이터로 index.html 생성됨".
- 회사 PC에서 Phase 2 시작 시 mock → production 스위치만 하면 곧바로 검증 가능한 상태로 인계.

### Phase 1 종료 — 첫 커밋 push 완료
- GitHub repo: https://github.com/poloth83/macro-dashboard
- 첫 커밋(5a0620d): 17 files, 1707 insertions. mock e2e 통과 상태.
- ust_core panel에 USGG3M Index 추가 (3M10Y slope derived 계산 위해).

---

## 다음 세션 시작 가이드

회사 PC에서 새 Claude Code 세션을 열 때 이 한 줄로 시작.

> "어제 시작한 매크로 대시보드 작업 이어서 진행. `plan.md`, `checklist.md`, `context-notes.md` 읽고 현재 상태 파악한 후, checklist에서 다음 미체크 항목부터 진행해줘. 현재는 회사 PC, Windows 10, Bloomberg Terminal 로그인된 상태."

이러면 Phase 2부터 자동으로 이어짐.

---

## 2026-05-10 — v2 골격 보강 시작

### 사용자 요청
- 이전 리뷰에서 제안한 수정사항과 추가 아이디어를 모두 반영 요청.

### 구현 범위
- 외부 CDN 제거. 회사망에서 `cdn.jsdelivr.net`이 막혀도 차트가 보이도록 서버 렌더링 SVG sparkline으로 전환.
- Bloomberg production 첫 연결을 위해 `--tickers smoke` 모드 추가.
- 핵심 티커 누락/관측치 부족/latest date 지연 시 조용히 HTML을 publish하지 않도록 품질 게이트 추가.
- 매크로 지표는 daily fill 통계가 왜곡될 수 있어 `frequency: release` 메타데이터를 추가하고 release 기준 통계로 분리.
- 실제 운용 포지션을 반영해 Futures, SOFR/FOMC, Credit Hedge, Macro Surprise/Reaction 패널을 추가.

### 제약
- 현재 macOS에는 Bloomberg Terminal이 없으므로 production mode는 실행 검증 불가.
- 일부 Bloomberg 티커는 회사 PC에서 `securityError`가 나올 수 있음. 이 경우 `bloomberg_tickers.yaml`에서 교체.

### 구현 결과
- Chart.js CDN 제거 완료. Sparkline은 `stats.py`에서 SVG polyline 좌표를 계산하고 template이 inline SVG로 렌더링.
- `fetch_bloomberg.py --tickers smoke` 추가. 회사 PC에서는 핵심 14개 티커만 먼저 가져와 Bloomberg 연결과 권한을 빠르게 확인.
- 필수 티커 품질 게이트 추가. required 티커가 비거나 관측치/stale 조건을 통과하지 못하면 snapshot 저장 전에 실패.
- macro series는 `frequency: release`를 부여해 forward-fill 일별 통계가 아니라 release 관측치 기준으로 percentile/z-score 계산.
- `UST Futures`, `SOFR / FOMC`, `Macro Surprise / Reaction` 패널 추가. Credit 패널은 LQD/HYG 외 OAS/CDX와 IG OAS vs equity beta derived 추가.
- mock 검증 결과.
  - `python fetch_bloomberg.py --mode dev --tickers smoke && python build_dashboard.py` 통과.
  - `python fetch_bloomberg.py --mode dev --tickers all && python build_dashboard.py` 통과.
  - full mock 기준 71개 unique ticker, 94개 metric card 렌더링.

---

## 2026-05-10 — Claude Code 전역 지침 이전 준비

### 사용자 요청
- 현재 Mac의 `/Users/yangtaehee/.claude/CLAUDE.md`를 회사 Windows PC에서도 그대로 설치할 수 있게 GitHub에 올려달라고 요청.

### 구현
- 원본 내용을 `agent-config/CLAUDE.md`에 그대로 추가.
- 회사 PC에서 `powershell -ExecutionPolicy Bypass -File scripts\install_claude_md.ps1` 한 번으로 `%USERPROFILE%\.claude\CLAUDE.md`에 설치되도록 스크립트 추가.
- 기존 회사 PC의 `CLAUDE.md`가 있으면 timestamp가 붙은 backup을 먼저 생성.

---

## 2026-05-11 — Phase 2 회사 PC 셋업

### 환경 확인
- Python 3.14.4, blpapi 3.26.3.1 이미 설치 상태. requirements.txt 의존성 전부 import 통과.
- Bloomberg Terminal 로그인 상태에서 `blpapi.Session()` 정상 시작.

### Smoke fetch 결과
- `--tickers smoke`로 8개 명시 + required 합쳐 14개 ticker 가져옴. 모두 842 obs (3Y + buffer).
- 최신 데이터 날짜 2026-05-11 = 오늘. stale 경고 0.

### 전체 fetch 결과 (71 tickers)
- 4개 invalid security 발견. 모두 non-required라 게이트 통과는 했지만 Phase 3에서 대체 ticker 식별 필요.
  - `ARDRESBO Index` — Fed 지급준비금 잔고.
  - `USTBTGA Index` — Treasury General Account.
  - `RRPONTSY Index` — Reverse Repo Operations.
  - `GDPNOW Index` — Atlanta Fed GDPNow.
- `IORB Index`는 fetch 자체는 성공했지만 last_val=110.43으로 금리(%) 단위와 불일치. 다른 Bloomberg ticker로 교체 필요 추정.

### 결정 1 — Windows 콘솔 UTF-8 reconfigure
- 증상: `build_dashboard.py` 마지막 `print("✓ done")`에서 `UnicodeEncodeError: 'cp949' codec`로 크래시. `fetch_bloomberg.py`의 한글 경고문은 콘솔에서 깨져 보임.
- 원인: Windows 한국어 로케일 cp949 콘솔이 UTF-8 문자 인코딩 못 함.
- 대응: 두 entry-point 스크립트 상단에 `sys.stdout.reconfigure(encoding="utf-8")`/`sys.stderr.reconfigure(encoding="utf-8")` 블록 추가. Python 3.7+ 표준 API.
- HTML 파일은 이미 `encoding="utf-8"`로 쓰고 있어 데이터 손상은 없었음. 콘솔 출력만 문제.

### 다음 우선순위 (Phase 3 시작 전)
1. 사내 IP HTTP 서버 띄워 동료 PC 접속 확인.
2. 운용역 시각 검증 — invalid 4종 ticker 교체 + IORB 값 단위 점검.
3. percentile/z-score 결과를 며칠 누적해서 보고 윈도우 사이즈 검토.

### 핸드오프 (2026-05-11, CLI Claude Code → VS Code Claude Code)
- **인계 시점 상태**: 4개 파일 modified, 미커밋. `build_dashboard.py` / `fetch_bloomberg.py` / `checklist.md` / `context-notes.md`.
- **막힌 이유**: 회사 PC에 git identity 미설정 (`user.email`, `user.name`). CLAUDE.md "NEVER update git config" 규칙 때문에 에이전트가 직접 못 세팅. 사용자가 다음 명령 한 번 실행하면 풀림.
  ```
  git config user.email "poloth@naver.com" && git config user.name "poloth83"
  ```
- **그 뒤 이어서 할 일**:
  1. `git add build_dashboard.py fetch_bloomberg.py checklist.md context-notes.md` 후 commit (메시지는 "Phase 2 회사 PC 셋업 완료 + Windows 콘솔 UTF-8 수정" 골자로).
  2. `python -m http.server 8000 --directory output` 백그라운드 실행. 사내 IP는 `ipconfig`로 확인 후 동료에게 공유.
  3. checklist Phase 2 마지막 항목 체크 처리.
- **검증 끝난 사실**: blpapi production fetch 통과 (71 ticker, smoke 14 ticker, 4 invalid는 non-required라 게이트 통과). 빌드 후 `output/index.html` 208KB 생성.

---

## 2026-05-11 — Phase 3 진입 (1) Invalid ticker 5종 교체 + H.4.1 단위 보정

### 배경
- Phase 2에서 ARDRESBO / USTBTGA / RRPONTSY / GDPNOW 4종이 invalid security로 빈 시리즈로 들어왔고, IORB Index는 데이터는 들어왔지만 last=110.43으로 % 단위와 불일치.
- 사용자가 Bloomberg Terminal에서 직접 검색해 valid ticker 회신.

### 교체 매핑
| 의미 | 이전 ticker (invalid/이상) | 신규 ticker | 검증 값 (2026-05-11) |
|---|---|---|---|
| Fed Reserve Balances | `ARDRESBO Index` | `FARBRBFB Index` | 3,032 USD bn |
| Treasury General Account | `USTBTGA Index` | `FARBDTRS Index` | 878 USD bn |
| Overnight RRP | `RRPONTSY Index` | `FARWDEAL Index` | 1.63 USD bn |
| Atlanta GDPNow | `GDPNOW Index` | `GDGCAFJP Index` | 3.747 % |
| IORB | `IORB Index` (값 110.43) | `IRRBIOER Index` | 3.65 % |

### 결정 — yaml `scale` 필드 도입
- Fed H.4.1 시리즈(`FARBAST`, `FARBRBFB`, `FARBDTRS`, `FARWDEAL`)는 Bloomberg에서 **raw 단위가 USD millions**로 들어옴. label은 "USD bn"이라 1000배 차이.
- 옵션 A (yaml scale 필드 추가), B (label만 mn으로 변경), C (build에서 hard-coded scaling) 중 A 채택.
- 구현: yaml 각 series에 `scale: 0.001` 선택 필드. `collect_all_tickers`에서 추출하고 `save_snapshot`이 history value에 곱해서 저장. default 1.0이라 기존 ticker는 영향 없음.
- dev mock은 새 ticker 이름 분기(FARBRBFB/FARBDTRS/FARWDEAL)로 갱신 + base를 raw millions 단위로 조정해 production과 단위 체계 일관시킴.
- derived 식 3곳(`SOFR-IORB spread`, `SFR1-IORB gap`, `SFR2-IORB gap`)의 ticker 참조도 `IRRBIOER Index`로 일괄 갱신.

### 결정 — 셸 기본 `python`이 인접 프로젝트 venv를 가리킴
- 증상: `python fetch_bloomberg.py` 실행 시 `ModuleNotFoundError: No module named 'yaml'`.
- 원인: 셸 PATH 상의 `python`이 인접한 `macro_trade_ai/.venv`를 가리키고 있음. macro-dashboard deps는 자체 `macro-dashboard/.venv`에 설치됨.
- 대응: fetch/build 실행 시 항상 `.venv/Scripts/python.exe`로 명시 호출. `scripts/run_daily.bat`은 이미 venv 활성화 후 호출하므로 자동화 경로엔 영향 없음 (확인은 Phase 4에서).

### 검증 결과
- 재fetch: 71 ticker, errors=0, warnings=0.
- 5종 모두 합리적 값 + H.4.1 4종은 USD bn 단위로 표시됨.
- 재빌드 통과, `output/index.html` 갱신.

---

## 2026-05-11 — Phase 3 (2) Credit 패널 단위/티커 보정

### 배경
- 패널 A~H 운용역 시각 검증을 위해 모든 metric(71 ticker + 19 derived)을 표로 dump해 1차 sanity-check.
- Credit 패널에서 3가지 명백한 이상값 발견.

### 발견과 해법

| 메트릭 | 이상값 (직전) | 진단 | 해법 | 결과 |
|---|---|---|---|---|
| US IG OAS | 1bp | Bloomberg가 % 단위로 송신 (raw 0.77) | yaml `scale: 100` | 77bp |
| US HY OAS | 3bp | 위와 동일 (raw 2.66) | yaml `scale: 100` | 266bp |
| CDX HY 5Y | 107bp | `CDX HY CDSI GEN 5Y Corp`은 price quote (par+premium), spread 아님 | ticker `CDX HY CDSI GEN 5Y SPRD Corp`로 교체 | 323bp |

### 부수효과
- derived `IG OAS beta vs SPX/NDX/RTY` 3종이 -0.01 bp/%에서 -0.6~-0.9 bp/% 범위로 정상화 (음의 beta = 주식↑ → spread↓, 정상 관계).
- mock 분기에 LUACOAS/LF98OAS를 명시 분기로 분리해 base를 % 단위로 두고 production과 단위 체계 일관시킴. CDX는 base 그대로 bp.

### 나머지 패널 1차 검토 결과 (사용자 시각 검증 보조)
- UST 커브/슬로프/버터플라이, BEI/TIPS, Swap spread, 글로벌 듀레이션, FX, 매크로 release 지표 — 모두 합리적 범위.
- 운용역 시각 검증 자체는 여전히 사용자가 브라우저로 패널 레이아웃/색상까지 보면서 짚어야 할 영역.
