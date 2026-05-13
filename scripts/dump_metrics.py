# 운용역 시각 검증용. 모든 패널의 metric을 한 표로 콘솔에 출력
"""
build_dashboard와 동일 흐름으로 stats를 산출하되, HTML 대신 텍스트 표로 dump.
이상값(단위 오류, stale, 비현실적 range)을 한눈에 점검하기 위함.

사용 (macro-dashboard 폴더에서):
  .venv/Scripts/python.exe scripts/dump_metrics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import stats as stats_mod
from build_dashboard import (
    load_latest_snapshot,
    snapshot_to_series_map,
    compute_panels,
    compute_derivations,
)


def _fmt(v, unit):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if unit == "%":
        return f"{v:7.2f}%"
    if unit == "bp":
        return f"{v:6.0f}bp"
    if unit in ("USD bn", "USD"):
        return f"{v:9,.0f}"
    if unit == "JPY":
        return f"{v:7.2f}"
    if unit == "KRW":
        return f"{v:8.1f}"
    if unit in ("vol", "idx"):
        return f"{v:7.2f}"
    if unit == "px":
        return f"{v:8.3f}"
    if unit == "k":
        return f"{v:6,.0f}k"
    if unit == "pt":
        return f"{v:8,.1f}"
    if unit == "bp/%":
        return f"{v:6.2f}"
    return f"{v:8.2f}"


def _fmt_change(v, unit):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "    —"
    sign = "+" if v >= 0 else ""
    if unit == "%":
        return f"{sign}{v*100:5.0f}bp"
    if unit == "bp":
        return f"{sign}{v:5.0f}bp"
    return f"{sign}{v:7.2f}"


def _fmt_p(v):
    if v is None:
        return "  — "
    return f"{v:4.0f}%"


def _fmt_z(v):
    if v is None:
        return "   — "
    return f"{v:+5.2f}σ"


def main():
    snapshot = load_latest_snapshot()
    print(f"\n  snapshot date: {snapshot['date']}  mode: {snapshot.get('mode')}\n")

    series_map = snapshot_to_series_map(snapshot)
    panels = compute_panels(snapshot, series_map)
    derived = compute_derivations(series_map)

    # 헤더
    cols = ["panel/ticker", "label", "current", "1D", "1W", "1M", "%ile", "z", "Yr", "low52w", "high52w", "as_of"]
    fmt = "  {:<14} {:<26} {:>11} {:>9} {:>9} {:>9} {:>5} {:>7} {:>3} {:>11} {:>11} {:<12}"
    print(fmt.format(*cols))
    print("  " + "-" * 150)

    for panel in panels:
        for m in panel["metrics"]:
            print(fmt.format(
                panel["key"][:14],
                (m["label"] or "")[:26],
                _fmt(m["current"], m["unit"]),
                _fmt_change(m["change_1d"], m["unit"]),
                _fmt_change(m["change_1w"], m["unit"]),
                _fmt_change(m["change_1m"], m["unit"]),
                _fmt_p(m["percentile"]),
                _fmt_z(m["zscore"]),
                str(m["window_years"]),
                _fmt(m["low_52w"], m["unit"]),
                _fmt(m["high_52w"], m["unit"]),
                (m["as_of"] or "")[:12],
            ))

    print("\n  --- derived ---\n")
    for m in derived:
        print(fmt.format(
            "derived",
            (m["label"] or "")[:26],
            _fmt(m["current"], m["unit"]),
            _fmt_change(m["change_1d"], m["unit"]),
            _fmt_change(m["change_1w"], m["unit"]),
            _fmt_change(m["change_1m"], m["unit"]),
            _fmt_p(m["percentile"]),
            _fmt_z(m["zscore"]),
            str(m["window_years"]),
            _fmt(m["low_52w"], m["unit"]),
            _fmt(m["high_52w"], m["unit"]),
            (m["as_of"] or "")[:12],
        ))


if __name__ == "__main__":
    main()
