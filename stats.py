# 시계열 데이터에서 percentile, z-score, 변화율 등 정량 통계를 계산하는 모듈
"""
fetch_bloomberg.py가 저장한 raw JSON을 받아서, 패널별 메트릭에 대해
일관된 통계 세트(현재값, 1D/1W/1M Δ, percentile, z-score, 52W high/low, sparkline)를 산출.

build_dashboard.py가 이 결과를 받아 Jinja2 템플릿에 주입.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

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
    percentile: Optional[float]      # 0~100, window_years 기준
    zscore: Optional[float]
    window_years: int                # 3 or 5 등, 카드 라벨 동적 표시용
    high_52w: Optional[float]
    low_52w: Optional[float]
    sparkline_6m: list[float]        # 오래된 → 최신 순 (차트용)
    sparkline_points: str            # SVG polyline points
    sparkline_baseline_y: Optional[float]   # sparkline 영역 내 평균값의 y좌표 (없으면 None)
    as_of: Optional[str]             # ISO date
    frequency: str                   # daily | release
    change_1d_label: str
    change_1w_label: str
    change_1m_label: str

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


def _release_series(series: pd.Series) -> pd.Series:
    """발표 지표의 daily forward-fill 중복값을 제거해 실제 release 관측치에 가깝게 압축."""
    clean = series.dropna().sort_index()
    if clean.empty:
        return clean
    changed = clean.ne(clean.shift(1))
    return clean[changed]


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
    frequency: str = "daily",
    window_years: int = 3,
    window_52w_days: int = 252,
    window_6m_days: int = 126,
) -> MetricStats:
    """
    단일 시계열에 대해 표준 통계 세트를 계산한다.

    Args:
        timeseries: index가 datetime인 일별 시계열. 결측치는 그대로 두고 함수 내에서 처리.
        window_years: percentile/z-score 계산용 lookback. 정책금리·실질금리처럼
            사이클이 긴 메트릭은 5로, 기본은 3. release 빈도는 월 단위 12 obs/year로 환산.
    """
    def empty() -> MetricStats:
        return MetricStats(
            label=label, unit=unit, current=None,
            change_1d=None, change_1w=None, change_1m=None,
            percentile=None, zscore=None,
            window_years=window_years,
            high_52w=None, low_52w=None,
            sparkline_6m=[], sparkline_points="", sparkline_baseline_y=None, as_of=None,
            frequency=frequency,
            change_1d_label="Prev" if frequency == "release" else "1D",
            change_1w_label="5 rel" if frequency == "release" else "1W",
            change_1m_label="21 rel" if frequency == "release" else "1M",
        )

    if timeseries.empty:
        return empty()

    series = timeseries.sort_index()
    stats_series = _release_series(series) if frequency == "release" else series.dropna()
    if stats_series.empty:
        return empty()

    current = float(series.iloc[-1]) if not pd.isna(series.iloc[-1]) else None
    as_of = str(series.index[-1].date()) if hasattr(series.index[-1], "date") else str(series.index[-1])

    if frequency == "release":
        current = float(stats_series.iloc[-1]) if not pd.isna(stats_series.iloc[-1]) else current
        as_of = str(stats_series.index[-1].date()) if hasattr(stats_series.index[-1], "date") else str(stats_series.index[-1])
        window_stats = stats_series.tail(12 * window_years)
        window_52w = stats_series.tail(12)
        window_6m = stats_series.tail(12)
    else:
        window_stats = stats_series.tail(252 * window_years)
        window_52w = stats_series.tail(window_52w_days)
        window_6m = stats_series.tail(window_6m_days)

    spark_values = [float(x) if not pd.isna(x) else None for x in window_6m.tolist()]

    return MetricStats(
        label=label,
        unit=unit,
        current=current,
        change_1d=_safe_change(stats_series, 1),
        change_1w=_safe_change(stats_series, 5),
        change_1m=_safe_change(stats_series, 21),
        percentile=_percentile(window_stats, current) if current is not None else None,
        zscore=_zscore(window_stats, current) if current is not None else None,
        window_years=window_years,
        high_52w=float(window_52w.max()) if not window_52w.empty else None,
        low_52w=float(window_52w.min()) if not window_52w.empty else None,
        sparkline_6m=spark_values,
        sparkline_points=_sparkline_points(spark_values),
        sparkline_baseline_y=_sparkline_baseline_y(spark_values),
        as_of=as_of,
        frequency=frequency,
        change_1d_label="Prev" if frequency == "release" else "1D",
        change_1w_label="5 rel" if frequency == "release" else "1W",
        change_1m_label="21 rel" if frequency == "release" else "1M",
    )


def _sparkline_points(values: list[Optional[float]], width: int = 180, height: int = 36) -> str:
    """값 배열을 작은 SVG polyline 좌표 문자열로 변환."""
    clean = [(i, v) for i, v in enumerate(values) if v is not None and not pd.isna(v)]
    if len(clean) < 2:
        return ""
    nums = [v for _, v in clean]
    lo = min(nums)
    hi = max(nums)
    span = hi - lo
    x_den = max(len(values) - 1, 1)
    points = []
    for i, v in clean:
        x = i / x_den * width
        y = height / 2 if span == 0 else height - ((v - lo) / span * height)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _sparkline_baseline_y(values: list[Optional[float]], height: int = 36) -> Optional[float]:
    """sparkline 영역 내 6M 평균값의 y좌표. 현재값이 평균 위/아래 어디인지 한눈에."""
    clean = [v for v in values if v is not None and not pd.isna(v)]
    if len(clean) < 2:
        return None
    lo = min(clean)
    hi = max(clean)
    if hi == lo:
        return height / 2
    mean = sum(clean) / len(clean)
    return round(height - ((mean - lo) / (hi - lo) * height), 1)


def compute_panel(
    panel_name: str,
    series_map: dict[str, dict],
) -> dict:
    """
    한 패널 내의 모든 시리즈에 대해 compute_metric을 적용.

    Args:
        series_map: {ticker: {"label": str, "unit": str, "timeseries": pd.Series, "window_years": int,
                              "priority": int (optional), "headline": bool (optional)}, ...}

    Returns:
        {"name": panel_name, "metrics": [MetricStats.to_dict(), ...]}
    """
    metrics = []
    for ticker, info in series_map.items():
        m = compute_metric(
            label=info["label"],
            unit=info["unit"],
            timeseries=info["timeseries"],
            frequency=info.get("frequency", "daily"),
            window_years=int(info.get("window_years", 3)),
        )
        metrics.append(m.to_dict() | {
            "ticker": ticker,
            "priority": int(info.get("priority", 99)),
            "headline": bool(info.get("headline", False)),
            "decimals": info.get("decimals"),
        })
    return {"name": panel_name, "metrics": metrics}


def compute_derived(
    name: str,
    unit: str,
    formula_series: pd.Series,
    window_years: int = 3,
    priority: int = 99,
    headline: bool = False,
    decimals=None,
) -> dict:
    """파생 메트릭 (BTP-Bund, swap spread 등)도 동일 통계 세트로."""
    m = compute_metric(label=name, unit=unit, timeseries=formula_series, window_years=window_years)
    return m.to_dict() | {
        "ticker": name,
        "priority": int(priority),
        "headline": bool(headline),
        "decimals": decimals,
    }
