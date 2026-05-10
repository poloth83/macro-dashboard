# 시계열 데이터에서 percentile, z-score, 변화율 등 정량 통계를 계산하는 모듈
"""
fetch_bloomberg.py가 저장한 raw JSON을 받아서, 패널별 메트릭에 대해
일관된 통계 세트(현재값, 1D/1W/1M Δ, percentile, z-score, 52W high/low, sparkline)를 산출.

build_dashboard.py가 이 결과를 받아 Jinja2 템플릿에 주입.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Sequence, Optional

import numpy as np
import pandas as pd


@dataclass
class MetricStats:
    """단일 메트릭의 통계 결과. 템플릿에서 그대로 사용 가능한 형태."""
    label: str
    unit: str
    current: Optional[float]
    change_1d: Optional[float]
    change_1w: Optional[float]
    change_1m: Optional[float]
    percentile_3y: Optional[float]   # 0~100
    zscore_3y: Optional[float]
    high_52w: Optional[float]
    low_52w: Optional[float]
    sparkline_6m: list[float]        # 오래된 → 최신 순 (차트용)
    as_of: Optional[str]             # ISO date

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_change(series: pd.Series, days: int) -> Optional[float]:
    """series 마지막 값과 days 영업일 전 값의 차이. 부족하면 None."""
    if len(series) <= days:
        return None
    current = series.iloc[-1]
    past = series.iloc[-1 - days]
    if pd.isna(current) or pd.isna(past):
        return None
    return float(current - past)


def _percentile(series: pd.Series, current: float) -> Optional[float]:
    """현재값이 series 분포 내 몇 percentile인지. 0(최저) ~ 100(최고)."""
    clean = series.dropna()
    if len(clean) < 30:
        return None
    return float((clean <= current).sum() / len(clean) * 100.0)


def _zscore(series: pd.Series, current: float) -> Optional[float]:
    """현재값의 z-score = (current - mean) / std."""
    clean = series.dropna()
    if len(clean) < 30:
        return None
    std = clean.std()
    if std == 0 or pd.isna(std):
        return None
    return float((current - clean.mean()) / std)


def compute_metric(
    label: str,
    unit: str,
    timeseries: pd.Series,
    window_3y_days: int = 252 * 3,
    window_52w_days: int = 252,
    window_6m_days: int = 126,
) -> MetricStats:
    """
    단일 시계열에 대해 표준 통계 세트를 계산한다.

    Args:
        timeseries: index가 datetime인 일별 시계열. 결측치는 그대로 두고 함수 내에서 처리.
    """
    if timeseries.empty:
        return MetricStats(
            label=label, unit=unit, current=None,
            change_1d=None, change_1w=None, change_1m=None,
            percentile_3y=None, zscore_3y=None,
            high_52w=None, low_52w=None,
            sparkline_6m=[], as_of=None,
        )

    series = timeseries.sort_index()
    current = float(series.iloc[-1]) if not pd.isna(series.iloc[-1]) else None
    as_of = str(series.index[-1].date()) if hasattr(series.index[-1], "date") else str(series.index[-1])

    window_3y = series.tail(window_3y_days)
    window_52w = series.tail(window_52w_days)
    window_6m = series.tail(window_6m_days)

    return MetricStats(
        label=label,
        unit=unit,
        current=current,
        change_1d=_safe_change(series, 1),
        change_1w=_safe_change(series, 5),
        change_1m=_safe_change(series, 21),
        percentile_3y=_percentile(window_3y, current) if current is not None else None,
        zscore_3y=_zscore(window_3y, current) if current is not None else None,
        high_52w=float(window_52w.max()) if not window_52w.empty else None,
        low_52w=float(window_52w.min()) if not window_52w.empty else None,
        sparkline_6m=[float(x) if not pd.isna(x) else None for x in window_6m.tolist()],
        as_of=as_of,
    )


def compute_panel(
    panel_name: str,
    series_map: dict[str, dict],
) -> dict:
    """
    한 패널 내의 모든 시리즈에 대해 compute_metric을 적용.

    Args:
        series_map: {ticker: {"label": str, "unit": str, "timeseries": pd.Series}, ...}

    Returns:
        {"name": panel_name, "metrics": [MetricStats.to_dict(), ...]}
    """
    metrics = []
    for ticker, info in series_map.items():
        m = compute_metric(
            label=info["label"],
            unit=info["unit"],
            timeseries=info["timeseries"],
        )
        metrics.append(m.to_dict() | {"ticker": ticker})
    return {"name": panel_name, "metrics": metrics}


def compute_derived(
    name: str,
    unit: str,
    formula_series: pd.Series,
) -> dict:
    """파생 메트릭 (BTP-Bund, swap spread 등)도 동일 통계 세트로."""
    m = compute_metric(label=name, unit=unit, timeseries=formula_series)
    return m.to_dict() | {"ticker": name}
