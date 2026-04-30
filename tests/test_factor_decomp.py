"""Tests for factor decomposition."""

import pytest
import pandas as pd
import numpy as np

from src.attribution.factor_decomp import decompose_revenue_change, decompose_segments
from src.data.baseline import compute_baseline


class TestFactorDecomposition:
    def test_decompose_no_change(self):
        actual = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 5.0}
        baseline = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 5.0}
        result = decompose_revenue_change(actual, baseline)

        assert result["revenue_change"] == 0
        assert result["volume_effect"] == 0
        assert result["ecpm_effect"] == 0
        assert result["fill_effect"] == 0

    def test_decompose_ecpm_drop(self):
        # eCPM drops from $5 to $3 (40% drop)
        actual = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 3.0}
        baseline = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 5.0}

        # Expected: Rev_B = 10000*0.9*5/1000 = 45
        # Rev_T = 10000*0.9*3/1000 = 27
        # eCPM effect = 10000*0.9*(3-5)/1000 = -18
        result = decompose_revenue_change(actual, baseline)

        assert result["volume_effect"] == pytest.approx(0, abs=0.01)
        assert result["fill_effect"] == pytest.approx(0, abs=0.01)
        assert result["ecpm_effect"] == pytest.approx(-18.0, abs=0.01)
        assert result["revenue_change"] == pytest.approx(-18.0, abs=0.01)

    def test_decompose_volume_increase(self):
        # Impressions double
        actual = {"impressions": 20000, "fill_rate": 0.9, "ecpm": 5.0}
        baseline = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 5.0}

        # Volume effect = (20000-10000)*0.9*5/1000 = 45
        result = decompose_revenue_change(actual, baseline)

        assert result["volume_effect"] == pytest.approx(45.0, abs=0.01)
        assert result["ecpm_effect"] == pytest.approx(0, abs=0.01)
        assert result["fill_effect"] == pytest.approx(0, abs=0.01)

    def test_decompose_fill_rate_drop(self):
        actual = {"impressions": 10000, "fill_rate": 0.5, "ecpm": 5.0}
        baseline = {"impressions": 10000, "fill_rate": 0.9, "ecpm": 5.0}

        # Fill effect = 10000*(0.5-0.9)*5/1000 = -20
        result = decompose_revenue_change(actual, baseline)

        assert result["fill_effect"] == pytest.approx(-20.0, abs=0.01)

    def test_decompose_segments_with_sample_data(self, sample_df):
        target = pd.Timestamp("2026-01-16")
        baseline = compute_baseline(sample_df, target, "rolling_7d")
        result_df = decompose_segments(sample_df, target, baseline, top_n=3)

        assert not result_df.empty
        assert "segment" in result_df.columns
        assert "revenue_change" in result_df.columns
        assert "ecpm_effect" in result_df.columns
