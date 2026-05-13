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

---

## 2026-05-11 — Phase 3 (3) percentile/z-score 윈도우 메트릭별 분리

### 배경
- plan.md 결정 9: "기본 3Y, 정책금리·실질금리는 5Y 병기 (사이클이 더 길기 때문)".
- 기존 stats.py는 전 메트릭 3Y 단일 윈도우, template "3Y %ile"/"3Y z" 라벨 하드코딩.

### 결정 — 메트릭별 단일 윈도우 (병기 X)
- yaml series/derived에 선택 필드 `window_years` 추가. 미설정 시 3.
- 카드 라벨은 `{{ m.window_years }}Y %ile` / `{{ m.window_years }}Y z`로 동적.
- "병기"보다 단일 윈도우가 카드 정보량을 유지하면서도 plan 의도를 충족. 토글이 필요해지면 v2로 이월.

### 적용 범위 (정책금리 / 실질금리)
- liquidity 패널: SOFRRATE, IRRBIOER (모두 required true)
- sofr_fomc 패널: SFR1~SFR6 Comdty (6종, SFR1만 required)
- real_bei 패널: USGGT05Y, USGGT10Y
- derived 8종: SOFR-IORB spread, SFR1/2/3 implied rate, SFR1/2-IORB gap, 10Y/5Y Real (TIPS)
- 총 10 series + 8 derived = 18개 메트릭이 5Y 윈도우

### 코드 변경 핵심
- `stats.MetricStats`: `percentile_3y` → `percentile`, `zscore_3y` → `zscore`로 리네임. 윈도우가 동적이라 3Y가 불변 의미를 갖지 않음. `window_years` 필드 추가.
- `compute_metric`: 파라미터 `window_years: int = 3`. release 빈도는 12 obs/year로 환산해 `tail(12 * window_years)`.
- `fetch_bloomberg.DEFAULT_HISTORY_DAYS`: 252×3+30 → 252×5+30 (5Y 윈도우에 데이터 부족 방지). 실제 fetch 결과 1,382 obs.
- `templates/index.html.j2`: 패널 + derived 2곳에 동일 라벨 패턴 적용.

### 검증
- 재fetch+재빌드 quality 0/0.
- 18개 메트릭이 5Y로 표시됨을 dump로 확인.
- 의미 있는 변화 예: IORB z-score -1.65σ(3Y) → -0.01σ(5Y). 5Y 윈도우가 저금리 사이클까지 포함하면서 현재 3.65%가 평균에 가까운 위치로 재평가.

---

## 2026-05-12 — Phase 3 (4) FOMC implied path 검증 & SFR derived 제거

### 발견 (의미상 문제)
- 기존 derived: `SFR1/2/3 implied rate = 100 - SFR{N} Comdty`, `SFR1/2-IORB gap = (100 - SFR{N}) - IRRBIOER`.
- 카드 라벨이 "다음 FOMC implied rate"로 해석될 여지가 있었으나 사실 다름.
- 3M SOFR future 정산식 = **reference quarter 내 daily SOFR의 산술평균**. 즉 SFR1 implied는 "다음 IMM 분기(예: 2026-06-17 ~ 2026-09-15) 평균 SOFR"이고, 그 안에 보통 1~2개의 FOMC가 포함됨. 단일 회의 implied가 아님.
- 운용역이 "SFR1-IORB gap = -10bp"를 "다음 회의에서 10bp 인하 기대"로 읽으면 틀린 해석이 됨.

### 사용자 선택 — B-1만 시도 후 안 되면 중단
- 옵션 A(이름 보정), B-1(Bloomberg 내부 implied field 직접 조회), B-2(FF futures decomposition), D(제거) 중 B-1 우선 시도, fallback 없이 중단으로 결정.
- 디스플레이 의도는 12회 FOMC 커버 + 카드 N개 + 라인차트 1개였으나 데이터 확보가 선행 조건.

### B-1 probe 결과 (`scripts/probe_fomc_implied.py`)
- Phase 1 (apiFLDS FieldSearchRequest, 키워드 6종 FOMC/WIRP/MEETING_IMPLIED/IMPLIED_FED/FED_TARGET_PROB/OIS_IMPLIED): 모두 0 hit. FieldSearchRequest 스키마 호출이 부정확할 가능성도 있으나 0 결과 자체는 강한 신호.
- Phase 2 (ReferenceDataRequest, 17개 candidate field × 4 securities FDTR/FDTRMID/FEDL01/USRINDEX Index): 17개 전부 `Field not valid`. WIRP/MEETING/OIS_IMPLIED/25bp probability 계열 모두 인식 안 됨.
- 결론: entitlement 문제가 아니라 **Bloomberg API 구조상 WIRP-style 회의별 implied rate가 단일 field로 노출되지 않음**. WIRP는 Terminal 애플리케이션이 OIS 커브로부터 step-function 분해해 그리는 계산물.

### 결정 — D안 채택 (derived 제거)
- yaml `derived` 섹션에서 5종 제거: SFR1/2/3 implied rate + SFR1/2-IORB gap.
- 자리에는 사유 주석 남겨 미래 세션이 "왜 없는지" 즉시 파악하도록.
- sofr_fomc 패널의 SFR1~SFR6 Comdty raw 카드는 유지 (선물 가격 자체는 정확한 정보).
- probe 스크립트는 `scripts/probe_fomc_implied.py`에 유지 — 향후 다른 Bloomberg 필드 probe 시 재활용 가능.

### 검증
- 재빌드 통과. derived 카드 수 19 → 14. SFR 검색에 derived hit 0건.
- sofr_fomc 패널 SFR1~6 카드는 그대로 표시됨.

### 향후 (FOMC implied path 필요해지면)
- B-2 (FF futures decomposition) 경로. FF1~FF12 Comdty + FOMC 회의 일정으로 step-function 분해해 회의별 implied rate 산출. CME FedWatch 방식. 데이터는 100% 확보 가능, 구현량은 있음.

---

## 2026-05-13 — Phase 3 (5) 패널 A~H 시각 검증 1차 보정 4건

### 배경
- `scripts/dump_metrics.py`를 신규로 만들어 73 metric + 14 derived를 콘솔 한 표로 dump. 운용역 시각 검증의 베이스.
- 절대값/range 자체는 거의 다 합리적. 표시·구조 측면 4건 보정.

### 보정 1 — SFR 카드 변화량 정밀도 (px 3 decimal)
- 증상: `SOFR Fut 1st` 1D=`-0.00`, 1W=`+0.00` — 0.005 미만 변화가 fmt_change 2 decimal에서 가려져 운용역이 "정말 0인지 표시 한계인지" 구분 불가.
- 대응: `build_dashboard._fmt_change`에 `unit == "px"` 분기 추가, 3 decimal로.
- 결과: SFR2~6의 1W/1M 변화가 의미 있는 값으로 보임. SFR1 1D는 여전히 -0.00로 보이지만 이건 실제 변화가 0.0005 수준이라 3 decimal에서도 반올림되는 정상 케이스.

### 보정 2 — H.4.1 frequency=release
- 증상: Fed BS/Reserve Balances/TGA/Overnight RRP 4종이 매일 1D=+0bn로 표시. blpapi HistoricalDataRequest가 NON_TRADING_WEEKDAYS + PREVIOUS_VALUE로 fill해서 카드는 daily처럼 보이지만 실제 발표는 주 1회(목).
- 대응: yaml 4종에 `frequency: release` + `stale_days: 14` + `min_obs: 52` 추가.
- 결과: 1D=`Prev` 라벨로 직전 release 대비 변화로 표시 (Fed BS +9.56bn, Reserve +113.99bn, TGA -104.17bn, RRP +0.89bn). as_of도 2026-05-06(최근 목요일)로 정확. percentile/z-score도 release 단위 통계로 의미 있는 값 산출. 단, stats.compute_metric의 release tail이 12*window_years로 월 기준 hard-coded라 주별 데이터엔 다소 좁은 윈도우(3Y면 36 obs ≈ 9개월). 통계 정밀도 한계는 수용 — H.4.1의 운용 가치는 절대 수준과 추세에 있고 percentile은 보조적.

### 보정 3 — swap_spread 패널명 정리
- 증상: 패널명이 "Swap Spread & Funding"인데 정작 카드는 swap rate 4종. 진짜 스왑스프레드는 derived 섹션. 운용역 기대 미스매치.
- 대응: 패널명을 "SOFR Swap Rates"로 단순화. 패널 key(`swap_spread`)는 derived의 swap spread 카드와 코드상 분리되어 영향 없음. 진짜 스왑스프레드 4종(2/5/10/30Y)은 derived 그대로.

### 보정 4 — 주식 200dma 이격도 derived 추가
- 증상: SPX/NDX/RTY raw level의 3Y percentile은 강세 추세장에서 구조적으로 100%·+2σ에 깔림. 운용역이 "항상 +2σ"로 학습되면 신호 가치 소실.
- 대응: derived에 `type: "ma_distance"` 신규 (build_dashboard에 `_ma_distance` 함수 + 분기). SPX/NDX/RTY 200dma 이격도(=(price - 200dma) / 200dma * 100) 3종 추가. unit 신규 `dev%` 도입 (fmt_value: `+X.X%`, fmt_change: `+X.XXpp`) — fmt에서 % 단위 ×100 bp 변환과 분리.
- 결과: SPX +9.23% (63% percentile, +0.48σ), NDX +16.74% (93%, +1.19σ), RTY +13.24% (93%, +1.25σ). raw level의 100%/+2σ 깔림과 비교해 사이클 위치 판단이 훨씬 명확.

### 검증
- 재빌드 통과. dump로 4건 모두 의도대로 반영 확인.
- 신규 자산: `scripts/dump_metrics.py`(향후 시각 검증 재활용용).
