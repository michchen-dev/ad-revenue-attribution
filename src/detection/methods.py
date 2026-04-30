"""Statistical anomaly detection methods for ad revenue time series."""

import pandas as pd
import numpy as np
from scipy import stats


def detect_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Modified Z-Score using Median Absolute Deviation (robust to outliers).

    Returns boolean mask where True = anomaly.
    """
    median = series.median()
    mad = np.median(np.abs(series - median))
    if mad == 0:
        return pd.Series(False, index=series.index)
    modified_z = 0.6745 * (series - median) / mad
    return np.abs(modified_z) > threshold


def detect_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """IQR-based outlier detection."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    return (series < lower) | (series > upper)


def detect_rolling_deviation(series: pd.Series, window: int = 7, n_std: float = 2.0) -> pd.Series:
    """Flag points that deviate significantly from rolling mean."""
    rolling_mean = series.rolling(window, center=True, min_periods=3).mean()
    rolling_std = series.rolling(window, center=True, min_periods=3).std()
    deviation = np.abs(series - rolling_mean)
    return deviation > (n_std * rolling_std)


def detect_period_over_period(series: pd.Series, period: int = 7, threshold_pct: float = 0.20) -> pd.Series:
    """Flag points with large period-over-period change (e.g., same day last week)."""
    pct_change = series.pct_change(periods=period).abs()
    return pct_change > threshold_pct


def detect_grubbs(series: pd.Series, alpha: float = 0.05) -> pd.Series:
    """Grubbs' test for outliers (assumes normality)."""
    result = pd.Series(False, index=series.index)
    if len(series) < 3:
        return result

    z = np.abs(series - series.mean()) / series.std()
    n = len(series)
    t_crit = stats.t.ppf(1 - alpha / (2 * n), n - 2)
    threshold = ((n - 1) / np.sqrt(n)) * np.sqrt(t_crit ** 2 / (n - 2 + t_crit ** 2))
    return z > threshold


ALL_METHODS = {
    "zscore": ("Modified Z-Score (MAD)", detect_zscore),
    "iqr": ("IQR 四分位距", detect_iqr),
    "rolling_deviation": ("移动平均偏离", detect_rolling_deviation),
    "period_over_period": ("周期对比 (WoW)", detect_period_over_period),
    "grubbs": ("Grubbs 检验", detect_grubbs),
}
