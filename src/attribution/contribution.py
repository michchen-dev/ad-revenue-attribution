"""Contribution decomposition: attribute revenue change to dimension segments."""

import pandas as pd
import numpy as np


def compute_contributions(df: pd.DataFrame, target_date, baseline_df: pd.DataFrame,
                          dimensions: list = None) -> dict:
    """Compute per-segment contribution to total revenue change.

    Args:
        df: Full dataset
        target_date: The anomaly date
        baseline_df: Baseline period data
        dimensions: Dimension columns to decompose (default: all available)

    Returns:
        {
            "total_change": float,
            "total_change_pct": float,
            "baseline_revenue": float,
            "actual_revenue": float,
            "segments": [
                {"dim": "channel", "value": "AdMob", "contribution": -5000, "contribution_pct": -60.0},
                ...
            ]
        }
    """
    target = pd.Timestamp(target_date)
    if dimensions is None:
        available = [d for d in ["channel", "geo", "ad_format"] if d in df.columns]
    else:
        available = [d for d in dimensions if d in df.columns]

    actual_day = df[df["date"] == target]
    actual_revenue = actual_day["revenue"].sum()

    # Baseline: average daily revenue over baseline period
    baseline_days = baseline_df["date"].nunique() or 1
    baseline_revenue = baseline_df["revenue"].sum() / baseline_days

    total_change = actual_revenue - baseline_revenue
    total_change_pct = (total_change / baseline_revenue * 100) if baseline_revenue > 0 else 0

    # Per-dimension decomposition
    segments = []
    for dim in available:
        actual_by_dim = actual_day.groupby(dim)["revenue"].sum()
        baseline_by_dim = baseline_df.groupby(dim)["revenue"].sum() / baseline_days

        for val in actual_by_dim.index.union(baseline_by_dim.index):
            a = actual_by_dim.get(val, 0)
            b = baseline_by_dim.get(val, 0)
            contrib = a - b
            contrib_pct = (contrib / total_change * 100) if abs(total_change) > 1e-6 else 0

            segments.append({
                "dim": dim,
                "value": str(val),
                "actual": round(a, 2),
                "baseline": round(b, 2),
                "contribution": round(contrib, 2),
                "contribution_pct": round(contrib_pct, 1),
            })

    # Sort by absolute contribution
    segments.sort(key=lambda s: abs(s["contribution"]), reverse=True)

    return {
        "total_change": round(total_change, 2),
        "total_change_pct": round(total_change_pct, 1),
        "baseline_revenue": round(baseline_revenue, 2),
        "actual_revenue": round(actual_revenue, 2),
        "segments": segments,
    }
