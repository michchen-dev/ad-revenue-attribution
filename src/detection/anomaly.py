"""Anomaly detection orchestrator: runs multiple methods, merges with voting."""

import pandas as pd
import numpy as np
from src.detection.methods import ALL_METHODS


def detect_anomalies(daily_df: pd.DataFrame, enabled_methods: list = None,
                     sensitivity: float = 1.0, min_agreement: int = 2) -> pd.DataFrame:
    """Run multi-method anomaly detection on daily revenue data.

    Args:
        daily_df: Daily aggregated DataFrame with 'date' and 'revenue' columns
        enabled_methods: List of method keys to enable (default: all)
        sensitivity: Multiplier for detection thresholds (lower = more sensitive)
        min_agreement: Minimum number of methods that must agree to flag an anomaly

    Returns:
        DataFrame of detected anomalies with metadata
    """
    if enabled_methods is None:
        enabled_methods = list(ALL_METHODS.keys())

    revenue = daily_df.set_index("date")["revenue"]
    votes = pd.DataFrame(index=revenue.index)
    details = {}

    for method_key in enabled_methods:
        name, func = ALL_METHODS[method_key]
        try:
            if method_key in ("zscore", "grubbs"):
                threshold = 3.0 / sensitivity if method_key == "zscore" else 0.05 * sensitivity
                mask = func(revenue, threshold=threshold)
            elif method_key == "iqr":
                mask = func(revenue, multiplier=1.5 / sensitivity)
            elif method_key == "rolling_deviation":
                mask = func(revenue, n_std=2.0 / sensitivity)
            elif method_key == "period_over_period":
                mask = func(revenue, threshold_pct=0.20 / sensitivity)
            else:
                mask = func(revenue)

            votes[name] = mask.astype(int)
            details[name] = mask
        except Exception:
            votes[name] = 0

    votes["agreement"] = votes.sum(axis=1)
    votes["is_anomaly"] = votes["agreement"] >= min_agreement

    # Build anomaly records
    anomalies = []
    for date_idx in votes[votes["is_anomaly"]].index:
        current_rev = revenue.loc[date_idx]
        rolling = revenue.shift(1).rolling(7).mean().loc[date_idx]
        change_pct = (current_rev - rolling) / rolling * 100 if pd.notna(rolling) and rolling > 0 else 0

        methods_flagged = [m for m in details if details[m].get(date_idx, False)]

        anomalies.append({
            "date": date_idx,
            "revenue": current_rev,
            "baseline": rolling if pd.notna(rolling) else None,
            "change_pct": round(change_pct, 1),
            "direction": "up" if change_pct > 0 else "down",
            "severity": min(votes.loc[date_idx, "agreement"] / len(enabled_methods), 1.0),
            "methods_flagged": methods_flagged,
        })

    result = pd.DataFrame(anomalies)
    if not result.empty:
        result = result.sort_values("severity", ascending=False).reset_index(drop=True)

    return result
