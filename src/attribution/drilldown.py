"""Recursive hierarchical drill-down attribution engine.

Given an anomaly, recursively drill down by available dimensions
to find the most specific root cause segments.
"""

import pandas as pd
import numpy as np


def drilldown(df: pd.DataFrame, target_date, baseline_df: pd.DataFrame,
              dimensions: list = None, threshold_pct: float = 5.0,
              max_depth: int = 3) -> dict:
    """Recursive drill-down into the attribution tree.

    Args:
        df: Full dataset
        target_date: Anomaly date
        baseline_df: Baseline period
        dimensions: Ordered list of dimensions to drill by (default: channel -> geo -> ad_format)
        threshold_pct: Minimum contribution % to continue drilling into a segment
        max_depth: Maximum recursion depth

    Returns:
        Nested attribution tree dict
    """
    if dimensions is None:
        dimensions = [d for d in ["channel", "geo", "ad_format"] if d in df.columns]

    if not dimensions or max_depth == 0:
        return {}

    target = pd.Timestamp(target_date)
    actual_day = df[df["date"] == target]
    dim = dimensions[0]
    baseline_days = baseline_df["date"].nunique() or 1

    tree = {}
    actual_by_dim = actual_day.groupby(dim)["revenue"].sum()
    baseline_by_dim = baseline_df.groupby(dim)["revenue"].sum() / baseline_days
    total_change = actual_day["revenue"].sum() - baseline_df["revenue"].sum() / baseline_days

    for val in actual_by_dim.index:
        a = actual_by_dim.get(val, 0)
        b = baseline_by_dim.get(val, 0)
        contrib = a - b
        contrib_pct = (contrib / total_change * 100) if abs(total_change) > 1e-6 else 0

        if abs(contrib_pct) < threshold_pct:
            continue

        # Factor decomposition for this segment
        from src.attribution.factor_decomp import decompose_revenue_change

        seg_actual = actual_day[actual_day[dim] == val]
        seg_baseline = baseline_df[baseline_df[dim] == val]
        seg_b_days = seg_baseline["date"].nunique() or 1

        actual_agg = {
            "impressions": seg_actual["impressions"].sum(),
            "fill_rate": seg_actual["fill_rate"].mean(),
            "ecpm": seg_actual["ecpm"].mean(),
        }
        baseline_agg = {
            "impressions": seg_baseline["impressions"].sum() / seg_b_days,
            "fill_rate": seg_baseline["fill_rate"].mean(),
            "ecpm": seg_baseline["ecpm"].mean(),
        }

        factor_decomp = decompose_revenue_change(actual_agg, baseline_agg)

        node = {
            "contribution": round(contrib, 2),
            "contribution_pct": round(contrib_pct, 1),
            "actual_revenue": round(a, 2),
            "baseline_revenue": round(b, 2),
            "factor_decomp": factor_decomp,
        }

        # Recurse into next dimension
        seg_df = df[df[dim] == val]
        seg_baseline_df = baseline_df[baseline_df[dim] == val]
        children = drilldown(seg_df, target_date, seg_baseline_df,
                             [d for d in dimensions[1:] if d != dim],
                             threshold_pct, max_depth - 1)

        if children:
            node["children"] = children

        tree[f"{dim}={val}"] = node

    return tree


def full_attribution(df: pd.DataFrame, target_date, baseline_df: pd.DataFrame,
                     dimensions: list = None) -> dict:
    """Run complete attribution analysis: contributions + factor decomp + drilldown tree.

    Returns a single nested dict suitable for visualization and export.
    """
    from src.attribution.contribution import compute_contributions

    target = pd.Timestamp(target_date)
    actual_rev = df[df["date"] == target]["revenue"].sum()
    baseline_days = baseline_df["date"].nunique() or 1
    baseline_rev = baseline_df["revenue"].sum() / baseline_days

    contrib = compute_contributions(df, target_date, baseline_df, dimensions)
    tree = drilldown(df, target_date, baseline_df, dimensions)

    return {
        "target_date": target_date,
        "actual_revenue": round(actual_rev, 2),
        "baseline_revenue": round(baseline_rev, 2),
        "total_change": round(actual_rev - baseline_rev, 2),
        "total_change_pct": round((actual_rev - baseline_rev) / baseline_rev * 100, 1) if baseline_rev > 0 else 0,
        "segments": contrib["segments"],
        "attribution_tree": tree,
    }
