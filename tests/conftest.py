"""Shared test fixtures."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_daily_df():
    """90 days of daily revenue with a planted anomaly on day 45."""
    dates = pd.date_range("2026-01-01", periods=90, freq="D")
    np.random.seed(42)
    revenue = 5000 + np.random.normal(0, 500, 90)
    # Planted drop
    revenue[45] = 2500
    # Weekend bumps
    for i in range(90):
        if dates[i].dayofweek >= 5:
            revenue[i] *= 1.15

    return pd.DataFrame({"date": dates, "revenue": revenue})


@pytest.fixture
def sample_df():
    """Multi-dimensional sample data."""
    records = []
    for day in range(30):
        for ch in ["AdMob", "Unity"]:
            for geo in ["US", "IN"]:
                records.append({
                    "date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=day),
                    "channel": ch,
                    "geo": geo,
                    "impressions": 10000 + day * 100,
                    "revenue": 50.0 + day * 0.5,
                    "ecpm": 5.0,
                    "fill_rate": 0.9,
                })

    df = pd.DataFrame(records)
    # Plant anomaly: day 15, US AdMob revenue drops 50%
    mask = (df["date"] == pd.Timestamp("2026-01-16")) & (df["geo"] == "US") & (df["channel"] == "AdMob")
    df.loc[mask, "revenue"] *= 0.5
    df.loc[mask, "ecpm"] *= 0.5
    return df
