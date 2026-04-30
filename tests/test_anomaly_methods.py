"""Tests for anomaly detection methods."""

import pytest
import pandas as pd
import numpy as np

from src.detection.methods import (
    detect_zscore, detect_iqr, detect_rolling_deviation,
    detect_period_over_period,
)
from src.detection.anomaly import detect_anomalies


class TestDetectionMethods:
    def test_zscore_detects_outlier(self, sample_daily_df):
        mask = detect_zscore(sample_daily_df["revenue"], threshold=3.0)
        assert mask[45], "Modified Z-Score should detect the planted outlier on day 45"

    def test_zscore_normal_data(self):
        series = pd.Series([10, 11, 10, 12, 10, 11, 10, 11, 10, 12])
        mask = detect_zscore(series)
        assert not mask.any(), "Z-Score should not flag normal data"

    def test_iqr_detects_outlier(self, sample_daily_df):
        mask = detect_iqr(sample_daily_df["revenue"])
        assert mask[45], "IQR should detect the planted outlier"

    def test_rolling_deviation(self, sample_daily_df):
        mask = detect_rolling_deviation(sample_daily_df["revenue"])
        assert mask[45], "Rolling deviation should flag day 45"

    def test_period_over_period(self):
        # Create a clear WoW change
        series = pd.Series([100] * 7 + [200] + [100] * 6)
        mask = detect_period_over_period(series)
        assert mask.iloc[7], "WoW should flag a 100% increase"

    def test_detect_anomalies_orchestrator(self, sample_daily_df):
        anomalies = detect_anomalies(sample_daily_df, min_agreement=2)
        assert not anomalies.empty, "Should detect anomalies with 2-method agreement"
        assert 45 in [anomalies.iloc[i]["date"] for i in range(len(anomalies)) if isinstance(anomalies.iloc[i]["date"], pd.Timestamp)] or \
               any(anomalies["date"].dt.date == pd.Timestamp("2026-02-15").date()), \
               "Day 45 should be flagged"

    def test_anomaly_has_correct_fields(self, sample_daily_df):
        anomalies = detect_anomalies(sample_daily_df, min_agreement=1)
        if not anomalies.empty:
            row = anomalies.iloc[0]
            assert "date" in row.index
            assert "revenue" in row.index
            assert "direction" in row.index
            assert "severity" in row.index
            assert "methods_flagged" in row.index
