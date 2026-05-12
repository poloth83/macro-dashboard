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

## Phase 2 — 회사 PC 셋업 (Windows)

- [x] GitHub repo clone — `C:\Users\Hana_FI\claude code_ai\macro-dashboard\`
- [x] Python 3.14 설치 확인 (jinja2/pandas/numpy/pyyaml/scipy/blpapi 3.26.3.1 모두 import)
- [x] `pip install -r requirements.txt` (blpapi 포함)
- [x] Bloomberg Terminal 로그인 상태 확인 (smoke fetch 성공으로 검증)
- [x] `python fetch_bloomberg.py --mode production --tickers smoke` — 14개 티커 모두 842 obs 수신
- [x] 전체 fetch 1회 통과 → `data/2026-05-11.json` 생성 확인 (71개 ticker, 4개 invalid 경고만 발생)
- [x] `python build_dashboard.py` 통과 → `output/index.html` 생성 확인 (208KB)
- [x] Windows 콘솔 cp949 인코딩 충돌 해결 (build_dashboard.py / fetch_bloomberg.py 양쪽 stdout/stderr UTF-8 reconfigure)
- [x] 권한/티커명 오류 있으면 `bloomberg_tickers.yaml` 보정 (Phase 3에서 처리 완료 — Reserve Balances `FARBRBFB`, TGA `FARBDTRS`, RRP `FARWDEAL`, GDPNow `GDGCAFJP`, IORB `IRRBIOER`로 교체. H.4.1 4종은 raw millions라 `scale: 0.001` 적용해 USD bn으로 표시)
- [x] `python -m http.server 8000` 띄우고 사내 IP로 동료 PC에서 접속 확인 (2026-05-11, http://10.155.41.52:8000, 로컬 200 확인 / 동료 PC 접속은 사용자 검증 필요)

## Phase 3 — 데이터 검증 & 튜닝 (Windows)

- [x] Invalid ticker 5종 교체 (Reserve Balances / TGA / RRP / GDPNow / IORB) + H.4.1 단위(scale 0.001) 처리
- [x] Credit 패널 보정 — LUACOAS/LF98OAS는 raw가 %라 scale 100으로 bp 변환, CDX HY는 spread 버전 ticker(`CDX HY CDSI GEN 5Y SPRD Corp`)로 교체. IG OAS beta 3종도 자동 정상화
- [ ] 패널 A~H 각각 — 실데이터로 표시되는 값이 운용역 감각과 맞는지 검증 (Credit 외 나머지는 1차 dump에서 정상 범위 확인. 사용자 시각 검증 남음)
- [x] percentile/z-score 윈도우 적정성 검토 — 메트릭별 `window_years` 옵션 도입. 정책금리(SOFR/IORB/SFR1~6) + 실질금리(TIPS 5Y/10Y) + 관련 derived 8종을 `window_years: 5`로. fetch history도 5Y+buffer로 확장. 카드 라벨은 동적 ("3Y %ile"/"5Y %ile")
- [x] FOMC implied path 계산 로직 검증 — SFR{1,2,3} Comdty는 generic rolling 3M SOFR future라 "다음 IMM 분기 평균 SOFR"을 implied하지, "다음 FOMC implied rate"가 아님. WIRP-style 회의별 implied rate를 Bloomberg API로 받을 수 있는지 probe (`scripts/probe_fomc_implied.py`) 한 결과 apiFLDS 키워드 search 0 hit + 17개 candidate field 전부 `Field not valid`로 회사 entitlement 문제가 아니라 API 구조상 노출 안 됨 확인. → SFR derived 5종(SFR1/2/3 implied rate, SFR1/2-IORB gap) 제거. 정식 회의별 implied path가 필요해지면 향후 FF futures decomposition(B-2)으로 별도 진행
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
- [x] 커밋 및 GitHub push

## Phase 1.6 — Claude Code 전역 지침 이전

- [x] Mac의 `/Users/yangtaehee/.claude/CLAUDE.md` 위치 확인
- [x] 민감정보 키워드 간단 점검
- [x] `agent-config/CLAUDE.md`에 원본 추가
- [x] Windows 설치 스크립트 `scripts/install_claude_md.ps1` 추가
- [x] 커밋 및 GitHub push
