# Macro & Rates Dashboard — Plan

## 목적

해외채권 운용 데스크에서 매일 아침 7~8시(KST) 사이에 팀이 함께 보는 정량 대시보드.
- 운용역의 머릿속에 흩어져 있는 매크로/금리/FX/크레딧 점검 항목들을 한 화면에 통합.
- 단순 수치 나열이 아닌 **percentile / z-score / 6M-1Y trend**로 현재 위치를 정량화.
- 어제 자료와 비교 가능한 **history 스냅샷** 누적.

## 데이터 소스

**Bloomberg Terminal API (`blpapi`) 단일 소스.**
- LSEG MCP는 LFA API entitlement가 없어 제외 (5종 엔드포인트 모두 권한 거부 확인).
- Daloopa는 기업 펀더멘털 영역으로 본 프로젝트와 부적합.
- 보조 — UST 입찰 일정/결과는 TreasuryDirect 공개 API (네트워크 허용 시).

## 아키텍처

```
[회사 PC, Bloomberg Terminal 로그인]
   │
   ├─ 06:30 KST  Windows 작업 스케줄러
   │
   ▼
[fetch_bloomberg.py]
   - blpapi로 티커별 latest + 3Y 일별 시계열 fetch
   - data/YYYY-MM-DD.json 저장
   │
   ▼
[build_dashboard.py]
   - 오늘/어제 JSON 로드
   - stats.py로 percentile, z-score, 1D/1W/1M 변화 계산
   - Jinja2 템플릿 렌더링
   - output/index.html (오늘) + output/history/YYYY-MM-DD.html (스냅샷)
   │
   ▼
[python -m http.server]  ← 본인 PC에서 단순 정적 서버
   │
   ▼
[팀원들이 사내 IP:포트 로 브라우저 접속]
```

## 패널 구조 (Tier 2 정적 사이트)

운용역 모니터 한 화면에 들어가는 그리드. 좌→우, 위→아래로 스캔.

### 헤드라인 (상단 고정)
- **Calendar** — 당일/금주 FOMC·ECB·BOJ·BOE 이벤트, 미국 지표 발표 시각, UST 입찰 일정.
- **Risk Regime Badge** — VIX, MOVE, S&P/Nasdaq/Russell 수익률, BTC 추세를 종합한 risk-on/off 시그널.
- **달러 유동성 게이지** — Fed BS 지급준비금, TGA, RRP, SOFR-IORB 스프레드 (수치 + 30일 변화).

### A. UST 코어 (포지션 1, 2, 7번 대응)
- 2Y/5Y/7Y/10Y/30Y 금리 — 현재값, 1D/1W/1M 변동, 3Y percentile, z-score.
- 2s10s, 5s30s, 3M10Y 슬로프 — 현재값, percentile, z-score, 6M 차트.
- 2/5/10 버터플라이 (body rich/cheap) — spread + z-score.
- SOFR 선물 implied path — FOMC별 implied rate vs 현재 IORB.

### B. 실질금리 & BEI
- 5Y/10Y 명목, BEI, 실질금리 분해 — 각 항목 percentile + z-score.
- 5Y5Y 실질금리 시계열 + r-star (NY Fed LW/HLW) 갭 차트.
- TIPS 커브 기울기.

### C. Swap Spread / Funding (포지션 3번)
- 2Y/5Y/10Y/30Y 스왑 스프레드 — 현재값, 1Y range, percentile, z-score.
- SOFR-IORB, GC repo, RRP 잔고 추이.

### D. 글로벌 듀레이션 (포지션 5번)
- US 10Y, Bund 10Y, BTP 10Y, OAT 10Y, JGB 10Y, Gilt 10Y/30Y.
- BTP-Bund spread, OAT-Bund spread — 현재값, z-score.
- JGB 30Y, Gilt 30Y — 재정 risk 스파이크 알람용 percentile.

### E. FX (포지션 4번)
- USDJPY, USDKRW spot — 현재값, 30D realized vol.
- US-JP, US-KR 2Y/10Y 금리차 vs spot 동조성 차트.

### F. Credit (포지션 6, 8번)
- LQD, HYG yield/spread vs UST 10Y → IG/HY OAS 추정.
- S&P/Nasdaq/Russell 일/주/월간 + 52주 위치.
- credit spread와 equity의 divergence z-score.

### G. 매크로 지표 핫리스트
지표별로 가장 최신 발표값, 컨센서스 대비 surprise, 12M 추이 미니차트, 다음 발표일.
- CPI, PPI, NFP, ADP, JOLTS, 신규/연속 실업수당
- ISM Manufacturing/Services PMI
- Michigan 심리·기대인플레
- Retail Sales (control group 강조)
- GDP 속보/잠정/확정, Atlanta Fed GDPNow

### H. UST 입찰 트래커
당일/익일 입찰 — 사이즈, 직전 입찰 결과 (bid-to-cover, indirect %, tail bps).

## 정량 분석 — 모든 메트릭에 공통 적용

각 지표/금리/스프레드에 대해 같은 통계 세트를 자동 계산.

| 항목 | 정의 |
|---|---|
| **Current** | 최신 종가 |
| **1D / 1W / 1M Δ** | 절대 변화 + bp/%/$ 단위 |
| **3Y percentile** | 최근 3년 일별 분포 내 위치 (0~100%) |
| **3Y z-score** | (현재 − 평균) / 표준편차 |
| **52W high/low** | 1년 최고/최저 |
| **6M sparkline** | 미니 라인차트 |

윈도우는 기본 3Y로 두되, 중앙은행 정책금리·실질금리는 5Y 병기.

## 자동화

- **회사 PC, Windows 작업 스케줄러** — 평일 06:30 KST에 `scripts/run_daily.bat` 실행.
- 실패 시 이메일/슬랙 알림은 Phase 4에서 추가.
- 주말은 데이터 변경 거의 없어 스킵.

## 결과물 위치

- 작업 디렉터리 — `~/macro-dashboard/` (macOS), `C:\Users\<user>\macro-dashboard\` (Windows).
- 정적 사이트 출력 — `output/` 폴더.
- 팀 공유 — 본인 PC에서 `python -m http.server 8000` → 동료는 `http://<본인PC사내IP>:8000` 접속.

## 무엇을 하지 않을 것

CLAUDE.md "Simplicity First" 원칙.
- React/Vue 등 SPA 프레임워크 사용 안 함 (Jinja2 + 정적 HTML로 충분).
- 데이터베이스 사용 안 함 (JSON 파일로 충분).
- 인증/권한 시스템 안 함 (사내망 내부 도구).
- 리얼타임 스트리밍 안 함 (장 마감 후 일별 스냅샷이면 충분).
- 알림/포지션 시그널 자동 생성 안 함 (1차 산출물은 "정량화된 점검표"까지).

## v2 보강 원칙

- 회사망에서 외부 CDN이 막혀도 동작하도록 대시보드는 로컬 asset 또는 inline SVG만 사용.
- Bloomberg production 데이터는 핵심 티커가 비어 있으면 HTML publish를 실패시킴.
- 금리/FX/주가처럼 매일 거래되는 시계열과 CPI/NFP/ISM처럼 발표일에만 갱신되는 macro release는 통계 계산 방식을 분리.
- 포지션과 직접 연결되는 패널을 우선 배치.
  - UST futures: 계약별 yield/future proxy, DV01 환산용 데이터.
  - SOFR/FOMC: SOFR futures strip, IORB 대비 gap.
  - Credit hedge: OAS/CDX/ETF proxy, equity index hedge beta.
  - Macro reaction: surprise와 당일 시장 반응을 같은 카드에서 점검.
