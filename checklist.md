# Macro & Rates Dashboard — Checklist

진행하면서 체크. 새 세션 시작할 때 이 파일에서 다음 미체크 항목부터 이어가면 됨.

## Phase 0 — 합의 (완료)

- [x] 패널 구조 합의 (A~H + 헤드라인)
- [x] 데이터 소스 결정 (Bloomberg 단일)
- [x] 결과물 형태 결정 (Tier 2 정적 사이트)
- [x] 호스팅 방식 결정 (본인 PC HTTP 서버)
- [x] 빌드 스택 결정 (Python + Jinja2)
- [x] 자동화 시점 결정 (06:30 KST)
- [x] 디바이스 합의 (개발 macOS, 운영 Windows 10)
- [x] 코드 이동 방식 결정 (GitHub Private repo)

## Phase 1 — 골격 (현재 세션, macOS)

블룸버그 없는 환경에서 만들 수 있는 것들. mock 데이터로 e2e 검증.

- [x] 폴더 구조 생성
- [x] `plan.md`
- [x] `checklist.md`
- [x] `context-notes.md`
- [x] `README.md`
- [x] `.gitignore`
- [x] `requirements.txt`
- [x] `bloomberg_tickers.yaml` (티커 dictionary)
- [x] `stats.py` (percentile / z-score / 변화율)
- [x] `fetch_bloomberg.py` (mock 모드 + production 모드 골격)
- [x] `build_dashboard.py` (Jinja2 렌더러)
- [x] `templates/index.html.j2` (Tier 2 레이아웃)
- [x] `assets/style.css` (다크 모드 스타일)
- [x] `scripts/run_daily.bat` (Windows 작업 스케줄러용)
- [x] `scripts/run_daily.sh` (macOS 테스트용)
- [x] mock 모드로 e2e 1회 통과 — `output/index.html` 생성 확인 (1912 lines, 66 metric cards)
- [x] 브라우저에서 레이아웃 확인 (사용자 검토)
- [x] git init + 첫 커밋
- [x] GitHub private repo 생성 및 push

## Phase 2 — 회사 PC 셋업 (Windows, 내일)

- [ ] GitHub repo clone — `C:\Users\<user>\macro-dashboard\`
- [ ] Python 3.11+ 설치 확인
- [ ] `pip install -r requirements.txt` (blpapi 포함)
- [ ] Bloomberg Terminal 로그인 상태 확인
- [ ] `python fetch_bloomberg.py --mode production --tickers smoke` 으로 5개 정도 핵심 티커만 fetch 시도
- [ ] 권한/티커명 오류 있으면 `bloomberg_tickers.yaml` 보정
- [ ] 전체 fetch 1회 통과 → `data/YYYY-MM-DD.json` 생성 확인
- [ ] `python build_dashboard.py` 통과 → `output/index.html` 생성 확인
- [ ] `python -m http.server 8000` 띄우고 사내 IP로 동료 PC에서 접속 확인

## Phase 3 — 데이터 검증 & 튜닝 (Windows)

- [ ] 패널 A~H 각각 — 실데이터로 표시되는 값이 운용역 감각과 맞는지 검증
- [ ] percentile/z-score 윈도우 적정성 검토 (3Y 기본 vs 5Y vs 1Y)
- [ ] FOMC implied path 계산 로직 검증
- [ ] 가중치 / 차트 스케일 / 색상 등 시각 튜닝
- [ ] 누락된 티커 추가 / 불필요한 티커 제거

## Phase 4 — 자동화 & 운영

- [ ] Windows 작업 스케줄러에 `scripts\run_daily.bat` 등록 (평일 06:30 KST)
- [ ] 실패 시 로그 파일에 기록 — `logs/YYYY-MM-DD.log`
- [ ] (선택) 슬랙 webhook으로 매일 06:35에 "오늘자 대시보드 → http://..." 푸시
- [ ] history 30일 누적 후 — 운용역 피드백 받아 v2 우선순위 결정
- [ ] (선택) UST 입찰 결과 자동 수집 (TreasuryDirect API)
- [ ] (선택) 컨센서스 surprise 추가 (Bloomberg ECO 함수 또는 별도 소스)

## Phase 1.5 — v2 골격 보강 (현재 세션, macOS)

운영 전 필수 안정화와 사용자가 요청한 추가 아이디어를 mock 환경에서 먼저 반영.

- [x] Chart.js CDN 제거 — 외부망 차단에도 sparkline 표시
- [x] `fetch_bloomberg.py --tickers smoke` 추가
- [x] 필수 티커/최소 관측치/latest date 품질 게이트 추가
- [x] 매크로 발표 지표를 release-frequency 통계로 분리
- [x] Windows 로그 파일명 locale 취약성 제거
- [x] Futures 패널 추가 — TU/FV/TY/US, DV01 환산용 데이터 골격
- [x] SOFR/FOMC 패널 추가 — SOFR futures strip, IORB gap
- [x] Credit 패널 보강 — OAS/CDX/ETF proxy와 equity hedge beta
- [x] Macro surprise/reaction 패널 골격 추가
- [x] mock e2e 재검증
- [ ] 커밋 및 GitHub push
