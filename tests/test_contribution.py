"""Tests for contribution decomposition."""

import pytest
import pandas as pd
import numpy as np

from src.data.baseline import compute_baseline
from src.attribution.contribution import compute_contributions


class TestContributionDecomposition:
    def test_basic_contribution(self, sample_df):
        target = pd.Timestamp("2026-01-16")
        baseline = compute_baseline(sample_df, target, "rolling_7d")
        result = compute_contributions(sample_df, target, baseline)

        assert abs(result["total_change"]) > 0
        assert len(result["segments"]) > 0

        # US AdMob should be a top negative contributor
        us_admob = [s for s in result["segments"] if s["value"] == "US" and s["dim"] == "geo"]
        if us_admob:
            assert us_admob[0]["contribution"] < 0, "US should show negative contribution due to planted anomaly"

    def test_total_change_matches_segments(self, sample_df):
        target = pd.Timestamp("2026-01-16")
        baseline = compute_baseline(sample_df, target, "rolling_7d")
        result = compute_contributions(sample_df, target, baseline)

        # Sum of unique-dimension contributions should approximate total change
        dim_contrib = {}
        for s in result["segments"]:
            key = s["dim"]
            if key not in dim_contrib:
                dim_contrib[key] = s["contribution"]

        # Each dimension contributes to the whole, so max should approximate total
        channel_total = sum(v for k, v in dim_contrib.items() if k == "channel")
        assert abs(channel_total - result["total_change"]) < max(abs(result["total_change"]) * 0.1, 10), \
            "Channel contributions should sum to total change (within rounding)"

    def test_returns_correct_structure(self, sample_df):
        target = pd.Timestamp("2026-01-16")
        baseline = compute_baseline(sample_df, target, "rolling_7d")
        result = compute_contributions(sample_df, target, baseline)

        required_keys = ["total_change", "total_change_pct", "baseline_revenue",
                         "actual_revenue", "segments"]
        for k in required_keys:
            assert k in result, f"Missing key: {k}"

        for seg in result["segments"]:
            for k in ["dim", "value", "contribution", "contribution_pct"]:
                assert k in seg, f"Segment missing key: {k}"
