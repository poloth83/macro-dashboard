# fetch된 일별 JSON 데이터를 stats로 가공하고 Jinja2 템플릿으로 렌더링해 정적 HTML 대시보드 생성
"""
입력 : data/YYYY-MM-DD.json (가장 최신 파일)
출력 :
  output/index.html                  ← 오늘 자 (덮어쓰기)
  output/history/YYYY-MM-DD.html     ← 일별 스냅샷 (누적)
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

import stats as stats_mod


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
HISTORY_DIR = OUTPUT_DIR / "history"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
TICKERS_PATH = ROOT / "bloomberg_tickers.yaml"

OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)


def load_latest_snapshot() -> dict:
    """data/ 폴더에서 가장 최근 JSON 파일을 로드."""
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"data/ 폴더에 JSON 파일이 없음. fetch_bloomberg.py 먼저 실행 필요.")
    latest = files[-1]
    print(f"  loading snapshot: {latest.name}")
    with latest.open(encoding="utf-8") as f:
        return json.load(f)


def snapshot_to_series_map(snapshot: dict) -> dict[str, pd.Series]:
    """JSON snapshot을 ticker → pd.Series 매핑으로 변환."""
    out: dict[str, pd.Series] = {}
    for panel in snapshot["panels"].values():
        for ticker, info in panel["tickers"].items():
            history = info["history"]
            if not history:
                out[ticker] = pd.Series([], dtype=float, name=ticker)
                continue
            idx = pd.to_datetime([h["date"] for h in history])
            vals = [h["value"] for h in history]
            out[ticker] = pd.Series(vals, index=idx, name=ticker)
    return out


def compute_panels(snapshot: dict, series_map: dict[str, pd.Series]) -> list[dict]:
    """snapshot의 패널 순서대로 stats 적용."""
    config = yaml.safe_load(TICKERS_PATH.read_text(encoding="utf-8"))
    panels_out = []

    for panel_key, panel_def in config["panels"].items():
        panel_data = snapshot["panels"].get(panel_key, {})
        series_for_panel = {}
        for s in panel_def["series"]:
            tk = s["ticker"]
            series_for_panel[tk] = {
                "label": s["label"],
                "unit": s["unit"],
                "timeseries": series_map.get(tk, pd.Series([], dtype=float)),
            }
        result = stats_mod.compute_panel(panel_def["name"], series_for_panel)
        result["key"] = panel_key
        panels_out.append(result)

    return panels_out


def compute_derivations(series_map: dict[str, pd.Series]) -> list[dict]:
    """bloomberg_tickers.yaml의 derived 섹션을 계산."""
    config = yaml.safe_load(TICKERS_PATH.read_text(encoding="utf-8"))
    derived_defs = config.get("derived", [])
    out = []

    for d in derived_defs:
        name = d["name"]
        unit = d["unit"]
        formula = d["formula"]
        try:
            series = _evaluate_formula(formula, series_map)
        except Exception as e:
            print(f"  ⚠ derived '{name}' 계산 실패: {e}", file=sys.stderr)
            continue
        # bp 단위는 100배 스케일 (백분율 차이를 bp로)
        if unit == "bp":
            series = series * 100.0
        out.append(stats_mod.compute_derived(name, unit, series))

    return out


def _evaluate_formula(formula: str, series_map: dict[str, pd.Series]) -> pd.Series:
    """
    아주 간단한 formula 인터프리터. 'TICKER A - TICKER B' 또는 '2*TICKER - TICKER - TICKER' 형태만 지원.
    완전한 expression parser는 과한 엔지니어링이라 skip — 필요 시 ast로 확장.
    """
    # 모든 ticker를 길이 내림차순으로 정렬해 longest-match 치환
    tickers_sorted = sorted(series_map.keys(), key=len, reverse=True)
    expr = formula
    placeholders: dict[str, pd.Series] = {}
    for i, tk in enumerate(tickers_sorted):
        if tk in expr:
            ph = f"__S{i}__"
            expr = expr.replace(tk, ph)
            placeholders[ph] = series_map[tk]

    # 모든 시리즈를 같은 index로 정렬
    if not placeholders:
        return pd.Series([], dtype=float)
    aligned = pd.DataFrame(placeholders).dropna(how="all")
    # 안전한 eval — placeholder만 허용
    local_ns = {ph: aligned[ph] for ph in placeholders}
    result = eval(expr, {"__builtins__": {}}, local_ns)
    return result


def render(snapshot_date: str, panels: list[dict], derived: list[dict]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["fmt"] = _fmt_value
    env.filters["fmt_change"] = _fmt_change
    env.filters["fmt_pct"] = _fmt_percentile
    env.filters["fmt_z"] = _fmt_zscore
    env.filters["color_z"] = _color_for_zscore

    template = env.get_template("index.html.j2")
    return template.render(
        snapshot_date=snapshot_date,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        panels=panels,
        derived=derived,
    )


# ---------------------------------------------------------------------------
# Jinja2 filters
# ---------------------------------------------------------------------------

def _fmt_value(v: Optional[float], unit: str = "") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if unit == "%":
        return f"{v:.2f}%"
    if unit == "bp":
        return f"{v:.0f}bp"
    if unit in ("USD bn", "USD"):
        return f"{v:,.0f}"
    if unit == "JPY":
        return f"{v:.2f}"
    if unit == "KRW":
        return f"{v:.1f}"
    if unit in ("vol", "idx"):
        return f"{v:.2f}"
    if unit == "k":
        return f"{v:,.0f}k"
    if unit == "pt":
        return f"{v:,.1f}"
    return f"{v:.2f}"


def _fmt_change(v: Optional[float], unit: str = "") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    sign = "+" if v >= 0 else ""
    if unit == "%":
        return f"{sign}{v*100:.0f}bp"   # 금리·BEI는 변화량을 bp로 표시
    if unit == "bp":
        return f"{sign}{v:.0f}bp"
    return f"{sign}{v:.2f}"


def _fmt_percentile(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.0f}%"


def _fmt_zscore(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:+.2f}σ"


def _color_for_zscore(v: Optional[float]) -> str:
    """z-score → CSS class name. 극단값 강조."""
    if v is None:
        return "z-na"
    if v >= 2.0:
        return "z-hot-high"
    if v >= 1.0:
        return "z-warm-high"
    if v <= -2.0:
        return "z-hot-low"
    if v <= -1.0:
        return "z-warm-low"
    return "z-neutral"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"[{datetime.now().isoformat(timespec='seconds')}] build_dashboard")

    snapshot = load_latest_snapshot()
    series_map = snapshot_to_series_map(snapshot)

    print(f"  computing panel stats...")
    panels = compute_panels(snapshot, series_map)
    derived = compute_derivations(series_map)

    print(f"  rendering...")
    html = render(snapshot["date"], panels, derived)

    # 오늘 자
    index_path = OUTPUT_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"  → {index_path}")

    # history 스냅샷
    history_path = HISTORY_DIR / f"{snapshot['date']}.html"
    history_path.write_text(html, encoding="utf-8")
    print(f"  → {history_path}")

    # assets 복사 (CSS 등)
    output_assets = OUTPUT_DIR / "assets"
    if output_assets.exists():
        shutil.rmtree(output_assets)
    shutil.copytree(ASSETS_DIR, output_assets)
    print(f"  → {output_assets}/")

    print("✓ done")


if __name__ == "__main__":
    main()
