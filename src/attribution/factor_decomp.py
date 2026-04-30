"""Factor decomposition: break revenue change into Volume/eCPM/Fill Rate effects.

Revenue = Impressions * Fill_Rate * eCPM / 1000

Using Shapley-style decomposition:
  Volume effect   = ΔImp * Fill_B * eCPM_B
  Fill effect     = Imp_B * ΔFill * eCPM_B
  eCPM effect     = Imp_B * Fill_B * ΔeCPM
  Interaction     = Revenue_change - Volume - Fill - eCPM
"""

import pandas as pd
import numpy as np


def decompose_revenue_change(actual_row: dict, baseline_row: dict) -> dict:
    """Decompose revenue change for a single segment into factor contributions.

    Args:
        actual_row: Dict with impressions, fill_rate, ecpm for the anomaly period
        baseline_row: Dict with impressions, fill_rate, ecpm for the baseline

    Returns:
        {
            "volume_effect": float,
            "ecpm_effect": float,
            "fill_effect": float,
            "interaction": float,
            "revenue_actual": float,
            "revenue_baseline": float,
            "revenue_change": float,
        }
    """
    imp_t = actual_row.get("impressions", 0)
    imp_b = baseline_row.get("impressions", 0)
    fill_t = actual_row.get("fill_rate", 0)
    fill_b = baseline_row.get("fill_rate", 0)
    ecpm_t = actual_row.get("ecpm", 0)
    ecpm_b = baseline_row.get("ecpm", 0)

    if imp_b == 0 or fill_b == 0 or ecpm_b == 0:
        return {
            "volume_effect": 0, "ecpm_effect": 0, "fill_effect": 0, "interaction": 0,
            "revenue_actual": 0, "revenue_baseline": 0, "revenue_change": 0,
        }

    rev_t = imp_t * fill_t * ecpm_t / 1000
    rev_b = imp_b * fill_b * ecpm_b / 1000

    # First-order effects (akin to Shapley with 3 players)
    volume_effect = (imp_t - imp_b) * fill_b * ecpm_b / 1000
    fill_effect = imp_b * (fill_t - fill_b) * ecpm_b / 1000
    ecpm_effect = imp_b * fill_b * (ecpm_t - ecpm_b) / 1000

    # Interaction / second-order (residual)
    interaction = (rev_t - rev_b) - volume_effect - fill_effect - ecpm_effect
    interaction = round(interaction, 2)

    return {
        "volume_effect": round(volume_effect, 2),
        "ecpm_effect": round(ecpm_effect, 2),
        "fill_effect": round(fill_effect, 2),
        "interaction": interaction,
        "revenue_actual": round(rev_t, 2),
        "revenue_baseline": round(rev_b, 2),
        "revenue_change": round(rev_t - rev_b, 2),
    }


def decompose_segments(df: pd.DataFrame, target_date, baseline_df: pd.DataFrame,
                       top_n: int = 5) -> pd.DataFrame:
    """Run factor decomposition for top-N contributing segments.

    Args:
        df: Full dataset
        target_date: Anomaly date
        baseline_df: Baseline period data
        top_n: Number of top segments to decompose

    Returns:
        DataFrame with factor decomposition results per segment
    """
    from src.attribution.contribution import compute_contributions

    contrib = compute_contributions(df, target_date, baseline_df)
    top_segments = contrib["segments"][:top_n]

    target = pd.Timestamp(target_date)
    actual_day = df[df["date"] == target]

    results = []
    for seg in top_segments:
        dim, val = seg["dim"], seg["value"]

        actual_seg = actual_day[actual_day[dim] == val]
        if actual_seg.empty:
            continue

        actual_agg = {
            "impressions": actual_seg["impressions"].sum(),
            "fill_rate": actual_seg["fill_rate"].mean(),
            "ecpm": actual_seg["ecpm"].mean(),
        }

        baseline_seg = baseline_df[baseline_df[dim] == val]
        if baseline_seg.empty:
            continue

        baseline_days = baseline_seg["date"].nunique() or 1
        baseline_agg = {
            "impressions": baseline_seg["impressions"].sum() / baseline_days,
            "fill_rate": baseline_seg["fill_rate"].mean(),
            "ecpm": baseline_seg["ecpm"].mean(),
        }

        decomp = decompose_revenue_change(actual_agg, baseline_agg)
        decomp["segment"] = f"{dim}={val}"
        decomp["contribution_pct"] = seg["contribution_pct"]
        results.append(decomp)

    return pd.DataFrame(results) if results else pd.DataFrame()
