# Macro & Rates Dashboard

해외채권 운용 데스크의 매일 아침 정량 점검 대시보드. Bloomberg Terminal API를 데이터 소스로 사용.

자세한 설계는 [`plan.md`](./plan.md), 진행 상태는 [`checklist.md`](./checklist.md), 결정 배경은 [`context-notes.md`](./context-notes.md) 참조.

---

## 빠른 시작 — macOS (mock 데이터)

블룸버그 없는 환경에서 레이아웃/렌더링 테스트.

```bash
cd ~/Desktop/Claude_workspace/macro-dashboard

# 가상환경
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치 (blpapi 제외 — macOS에선 실데이터 못 씀)
pip install jinja2 pandas numpy pyyaml

# mock 데이터로 fetch
python fetch_bloomberg.py --mode dev

# 대시보드 빌드
python build_dashboard.py

# 로컬 미리보기
cd output && python -m http.server 8000
# 브라우저에서 http://localhost:8000
```

---

## 빠른 시작 — Windows 회사 PC (실데이터)

### 1회성 셋업

```cmd
:: GitHub clone
cd C:\Users\<user>
git clone https://github.com/<user>/macro-dashboard.git
cd macro-dashboard

:: Python 3.11+ 설치 확인
python --version

:: 가상환경
python -m venv .venv
.venv\Scripts\activate

:: 의존성 설치 (blpapi 포함)
pip install -r requirements.txt
pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
```

### 매일 자동 실행 (Windows 작업 스케줄러)

`scripts\run_daily.bat`를 평일 06:30 KST에 트리거.

1. `taskschd.msc` 실행
2. 작업 만들기 → 평일 06:30 KST → `scripts\run_daily.bat` 실행
3. "사용자가 로그온할 때만 실행" 옵션 권장 (블룸버그 Terminal 로그인이 필요하므로)

### 팀 공유

```cmd
:: HTTP 서버 띄우기 (계속 실행 상태 유지)
cd output
python -m http.server 8000
```

동료들은 `http://<본인PC사내IP>:8000` 접속. 사내 IP는 `ipconfig`로 확인.

---

## 디렉터리 구조

```
macro-dashboard/
├── plan.md                  # 설계 문서
├── checklist.md             # 진행 상태
├── context-notes.md         # 결정 배경
├── README.md                # 이 파일
├── requirements.txt
├── .gitignore
├── bloomberg_tickers.yaml   # 패널별 블룸버그 티커 매핑
├── stats.py                 # percentile / z-score 계산
├── fetch_bloomberg.py       # 데이터 수집 (dev/production 모드)
├── build_dashboard.py       # Jinja2 렌더링
├── templates/
│   └── index.html.j2        # 대시보드 레이아웃
├── assets/
│   └── style.css            # 다크 모드 스타일
├── data/                    # 일별 raw JSON (gitignored)
├── output/                  # 생성된 HTML
│   ├── index.html           # 오늘 자
│   └── history/
│       └── 2026-05-10.html  # 일별 스냅샷
└── scripts/
    ├── run_daily.bat        # Windows용
    └── run_daily.sh         # macOS 테스트용
```

---

## 의도적으로 만들지 않은 것

- React/Vue 등 SPA — Jinja2 + 정적 HTML로 충분.
- DB — JSON 파일로 충분.
- 인증 — 사내망 내부 도구.
- 리얼타임 스트리밍 — 일별 스냅샷이 본 용도에 맞음.
- 자동 매매 시그널 — 1차 산출물은 정량 점검표까지.
