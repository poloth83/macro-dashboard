# 블룸버그 Terminal에서 매일 매크로/금리/FX/크레딧 데이터를 fetch해 일별 JSON으로 저장
"""
모드:
  --mode dev         : 블룸버그 없이 mock 데이터 생성 (macOS 개발/레이아웃 테스트용)
  --mode production  : 회사 PC에서 blpapi로 실데이터 fetch (Windows + Bloomberg Terminal)

출력:
  data/YYYY-MM-DD.json  — 모든 패널/티커의 3Y 일별 시계열 + 메타데이터
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


# ---------------------------------------------------------------------------
# 공통
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
TICKERS_PATH = ROOT / "bloomberg_tickers.yaml"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_HISTORY_DAYS = 252 * 3 + 30  # 3Y + buffer


def load_tickers_config() -> dict:
    with TICKERS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_all_tickers(config: dict) -> list[dict]:
    """모든 패널의 (panel_key, ticker, label, unit) 리스트로 평탄화."""
    flat = []
    for panel_key, panel in config["panels"].items():
        for s in panel["series"]:
            flat.append({
                "panel": panel_key,
                "panel_name": panel["name"],
                "ticker": s["ticker"],
                "label": s["label"],
                "unit": s["unit"],
            })
    return flat


# ---------------------------------------------------------------------------
# Mode: dev (mock 데이터)
# ---------------------------------------------------------------------------

def generate_mock_series(ticker: str, days: int = DEFAULT_HISTORY_DAYS) -> pd.Series:
    """
    티커 종류에 따라 그럴듯한 mock 시계열 생성.
    레이아웃/통계 로직 검증용. 실제 시장값과 무관.
    """
    rng = np.random.default_rng(seed=hash(ticker) & 0xFFFFFFFF)
    end = pd.Timestamp(date.today())
    dates = pd.bdate_range(end=end, periods=days)

    # 티커 카테고리별 base level과 변동성을 대충 분기
    if "USGG" in ticker or "GDBR" in ticker or "GBTPGR" in ticker or "GUKG" in ticker or "GJGB" in ticker:
        # 국채 금리 (%)
        base = rng.uniform(2.5, 5.0)
        steps = rng.normal(0, 0.03, days)
    elif "USOSFR" in ticker:
        base = rng.uniform(3.0, 5.0)
        steps = rng.normal(0, 0.03, days)
    elif "USYC" in ticker or "USGGBE" in ticker:
        base = rng.uniform(-50, 250) / 100
        steps = rng.normal(0, 0.04, days)
    elif "USDJPY" in ticker:
        base = rng.uniform(140, 160)
        steps = rng.normal(0, 0.4, days)
    elif "USDKRW" in ticker:
        base = rng.uniform(1300, 1450)
        steps = rng.normal(0, 4, days)
    elif "VIX" in ticker:
        base = 16
        steps = rng.normal(0, 0.8, days)
    elif "MOVE" in ticker:
        base = 90
        steps = rng.normal(0, 3, days)
    elif "SPX" in ticker:
        base = 5500
        steps = rng.normal(2, 50, days)
    elif "NDX" in ticker:
        base = 19000
        steps = rng.normal(8, 200, days)
    elif "RTY" in ticker:
        base = 2100
        steps = rng.normal(1, 25, days)
    elif "XBTUSD" in ticker:
        base = 70000
        steps = rng.normal(50, 1500, days)
    elif "FARBAST" in ticker:
        base = 7200
        steps = rng.normal(-1, 5, days)
    elif "ARDRESBO" in ticker:
        base = 3300
        steps = rng.normal(0, 15, days)
    elif "USTBTGA" in ticker:
        base = 750
        steps = rng.normal(0, 25, days)
    elif "RRPONTSY" in ticker:
        base = 400
        steps = rng.normal(-1, 30, days)
    elif "SOFRRATE" in ticker or "IORB" in ticker:
        base = 4.33
        steps = rng.normal(0, 0.005, days)
    elif "LQD" in ticker or "HYG" in ticker:
        base = 110 if "LQD" in ticker else 80
        steps = rng.normal(0.01, 0.4, days)
    elif "CPI" in ticker:
        base = 3.2
        steps = rng.normal(0, 0.05, days)
    elif "NFP" in ticker:
        base = 180
        steps = rng.normal(0, 30, days)
    elif "ADP" in ticker:
        base = 150
        steps = rng.normal(0, 25, days)
    elif "JOLT" in ticker:
        base = 8000
        steps = rng.normal(0, 200, days)
    elif "INJC" in ticker:
        base = 220
        steps = rng.normal(0, 8, days)
    elif "NAPM" in ticker:
        base = 50
        steps = rng.normal(0, 0.6, days)
    elif "CONS" in ticker:
        base = 70
        steps = rng.normal(0, 1.5, days)
    elif "RST" in ticker:
        base = 0.4
        steps = rng.normal(0, 0.3, days)
    elif "GDP" in ticker:
        base = 2.5
        steps = rng.normal(0, 0.2, days)
    else:
        base = 100
        steps = rng.normal(0, 1, days)

    values = base + np.cumsum(steps)
    return pd.Series(values, index=dates, name=ticker)


def fetch_dev(tickers: list[dict]) -> dict[str, pd.Series]:
    """모든 티커에 대해 mock 시계열 생성."""
    out = {}
    for t in tickers:
        out[t["ticker"]] = generate_mock_series(t["ticker"])
    return out


# ---------------------------------------------------------------------------
# Mode: production (blpapi)
# ---------------------------------------------------------------------------

def fetch_production(tickers: list[dict]) -> dict[str, pd.Series]:
    """
    회사 PC(Windows + Bloomberg Terminal)에서 실데이터 fetch.
    blpapi import는 이 함수 안에서만 — macOS에서는 import 자체가 실패하므로.
    """
    try:
        import blpapi
    except ImportError as e:
        raise RuntimeError(
            "blpapi import 실패. 회사 PC에서만 production 모드 사용 가능. "
            "설치: pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi"
        ) from e

    session = blpapi.Session()
    if not session.start():
        raise RuntimeError("blpapi session 시작 실패. Bloomberg Terminal이 로그인되어 있는지 확인.")
    if not session.openService("//blp/refdata"):
        raise RuntimeError("//blp/refdata 서비스 오픈 실패.")
    refdata = session.getService("//blp/refdata")

    end = date.today()
    start = end - timedelta(days=int(DEFAULT_HISTORY_DAYS * 1.5))  # 영업일 보정용 buffer
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    out: dict[str, pd.Series] = {}

    for t in tickers:
        ticker = t["ticker"]
        request = refdata.createRequest("HistoricalDataRequest")
        request.append("securities", ticker)
        request.append("fields", "PX_LAST")
        request.set("startDate", start_str)
        request.set("endDate", end_str)
        request.set("periodicitySelection", "DAILY")
        request.set("nonTradingDayFillOption", "NON_TRADING_WEEKDAYS")
        request.set("nonTradingDayFillMethod", "PREVIOUS_VALUE")

        session.sendRequest(request)

        records: list[tuple[date, float]] = []
        while True:
            ev = session.nextEvent(500)
            for msg in ev:
                if not msg.hasElement("securityData"):
                    continue
                sec_data = msg.getElement("securityData")
                if sec_data.hasElement("securityError"):
                    print(f"  ⚠ {ticker}: securityError — {sec_data.getElement('securityError')}", file=sys.stderr)
                    continue
                field_data = sec_data.getElement("fieldData")
                for i in range(field_data.numValues()):
                    point = field_data.getValue(i)
                    if not point.hasElement("PX_LAST"):
                        continue
                    d = point.getElementAsDatetime("date").date() if hasattr(point.getElementAsDatetime("date"), "date") else point.getElementAsDatetime("date")
                    v = point.getElementAsFloat("PX_LAST")
                    records.append((d, v))
            if ev.eventType() == blpapi.Event.RESPONSE:
                break

        if records:
            idx, vals = zip(*records)
            out[ticker] = pd.Series(vals, index=pd.to_datetime(idx), name=ticker)
        else:
            out[ticker] = pd.Series([], dtype=float, name=ticker)
            print(f"  ⚠ {ticker}: 데이터 없음", file=sys.stderr)

    session.stop()
    return out


# ---------------------------------------------------------------------------
# 저장
# ---------------------------------------------------------------------------

def save_snapshot(series_map: dict[str, pd.Series], tickers: list[dict], mode: str) -> Path:
    """
    오늘 자 JSON 스냅샷을 data/YYYY-MM-DD.json으로 저장.
    포맷:
    {
      "date": "2026-05-10",
      "mode": "dev" | "production",
      "panels": {
        "ust_core": {
          "name": "UST 코어",
          "tickers": {
            "USGG10YR Index": {
              "label": "UST 10Y", "unit": "%",
              "history": [{"date": "2023-01-03", "value": 3.65}, ...]
            }, ...
          }
        }, ...
      }
    }
    """
    config = load_tickers_config()

    panels_out: dict[str, dict] = {}
    for panel_key, panel in config["panels"].items():
        panels_out[panel_key] = {"name": panel["name"], "tickers": {}}
        for s in panel["series"]:
            tk = s["ticker"]
            ts = series_map.get(tk, pd.Series([], dtype=float))
            history = [
                {"date": str(d.date() if hasattr(d, "date") else d), "value": (None if pd.isna(v) else float(v))}
                for d, v in ts.items()
            ]
            panels_out[panel_key]["tickers"][tk] = {
                "label": s["label"],
                "unit": s["unit"],
                "history": history,
            }

    payload = {
        "date": str(date.today()),
        "mode": mode,
        "panels": panels_out,
    }

    out_path = DATA_DIR / f"{date.today().isoformat()}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch Bloomberg data for macro dashboard")
    parser.add_argument("--mode", choices=["dev", "production"], default="dev",
                        help="dev: mock 데이터 (macOS 개발용) / production: blpapi 실데이터 (Windows 회사 PC)")
    args = parser.parse_args()

    config = load_tickers_config()
    tickers = collect_all_tickers(config)

    print(f"[{datetime.now().isoformat(timespec='seconds')}] mode={args.mode}, tickers={len(tickers)}")

    if args.mode == "dev":
        series_map = fetch_dev(tickers)
    else:
        series_map = fetch_production(tickers)

    out_path = save_snapshot(series_map, tickers, args.mode)
    print(f"  saved → {out_path}")


if __name__ == "__main__":
    main()
