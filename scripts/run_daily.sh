#!/usr/bin/env bash
# macOS에서 mock 데이터로 e2e 테스트할 때 사용. 실운영은 Windows의 run_daily.bat.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -d .venv ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

mkdir -p logs
LOGFILE="logs/$(date +%Y-%m-%d).log"

{
    echo "=== $(date) ==="
    python fetch_bloomberg.py --mode dev
    python build_dashboard.py
    echo "OK"
} >> "$LOGFILE" 2>&1
