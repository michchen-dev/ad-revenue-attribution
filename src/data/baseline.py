"""Baseline period computation for comparison."""

import pandas as pd
import numpy as np


def compute_baseline(df: pd.DataFrame, target_date, method: str = "rolling_7d"):
    """Compute baseline revenue for a given date.

    Args:
        df: Full dataset with date column
        target_date: The anomaly date to compare against
        method: 'rolling_7d' (preceding 7 days), 'wow' (same day last week), 'month_avg' (30-day avg)

    Returns:
        DataFrame filtered to the baseline period
    """
    target = pd.Timestamp(target_date)

    if method == "rolling_7d":
        start = target - pd.Timedelta(days=7)
        end = target - pd.Timedelta(days=1)
        baseline = df[(df["date"] >= start) & (df["date"] <= end)]

    elif method == "wow":
        start = target - pd.Timedelta(days=7)
        baseline = df[df["date"] == start]

    elif method == "month_avg":
        start = target - pd.Timedelta(days=30)
        end = target - pd.Timedelta(days=1)
        baseline = df[(df["date"] >= start) & (df["date"] <= end)]

    else:
        raise ValueError(f"Unknown baseline method: {method}")

    return baseline


def aggregate_baseline(baseline: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """Aggregate baseline to daily averages by dimension."""
    if baseline.empty:
        return pd.DataFrame()

    days = baseline["date"].nunique() or 1
    agg = baseline.groupby(group_cols).agg(
        impressions=("impressions", lambda x: x.sum() / days),
        clicks=("clicks", lambda x: x.sum() / days) if "clicks" in baseline.columns else None,
        revenue=("revenue", lambda x: x.sum() / days),
        ecpm=("ecpm", "mean"),
        fill_rate=("fill_rate", "mean"),
    ).reset_index()

    return agg
