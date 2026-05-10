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

---

## 다음 세션 시작 가이드

회사 PC에서 새 Claude Code 세션을 열 때 이 한 줄로 시작.

> "어제 시작한 매크로 대시보드 작업 이어서 진행. `plan.md`, `checklist.md`, `context-notes.md` 읽고 현재 상태 파악한 후, checklist에서 다음 미체크 항목부터 진행해줘. 현재는 회사 PC, Windows 10, Bloomberg Terminal 로그인된 상태."

이러면 Phase 2부터 자동으로 이어짐.
