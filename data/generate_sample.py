"""Generate a 90-day sample ad revenue dataset with planted anomalies.

Revenue = Impressions * Fill_Rate * eCPM / 1000 (ad tech standard formula)

Anomalies planted:
  1. Day 45-47: US eCPM crashes 40% (AdMob bidding algorithm change)
  2. Day 60-61: IN fill_rate drops 30% (network outage)
  3. Day 75: BR impressions spike 50% (promotional campaign)
  4. Day 80: Overall revenue drops 25% across all channels (market holiday)
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

CHANNELS = ["AdMob", "Unity", "AppLovin", "ironSource"]
GEOS = ["US", "IN", "BR", "ID", "DE", "JP"]
AD_FORMATS = ["Banner", "Interstitial", "Rewarded", "Native"]

GEO_IMPRESSIONS_BASE = {"US": 500_000, "IN": 800_000, "BR": 300_000, "ID": 400_000, "DE": 200_000, "JP": 250_000}
GEO_ECPM_BASE = {"US": 8.50, "IN": 0.80, "BR": 1.20, "ID": 0.60, "DE": 5.50, "JP": 6.00}
GEO_FILL_RATE_BASE = {"US": 0.92, "IN": 0.78, "BR": 0.85, "ID": 0.72, "DE": 0.90, "JP": 0.88}

FORMAT_ECPM_MULT = {"Banner": 0.3, "Interstitial": 1.0, "Rewarded": 1.5, "Native": 0.7}
FORMAT_FILL_MULT = {"Banner": 1.0, "Interstitial": 0.95, "Rewarded": 0.90, "Native": 0.85}
FORMAT_IMPRESSIONS_SHARE = {"Banner": 0.50, "Interstitial": 0.10, "Rewarded": 0.15, "Native": 0.25}

records = []
start_date = pd.Timestamp("2026-01-01")

for day_offset in range(90):
    date = start_date + pd.Timedelta(days=day_offset)
    dow = date.dayofweek  # 0=Monday

    for channel in CHANNELS:
        ch_mult = {"AdMob": 1.0, "Unity": 0.7, "AppLovin": 0.5, "ironSource": 0.4}[channel]

        for geo in GEOS:
            # Base values with day-of-week seasonality (weekends +15% impressions)
            dow_mult = 1.15 if dow >= 5 else 1.0
            imp_base = GEO_IMPRESSIONS_BASE[geo] * ch_mult * dow_mult
            ecpm_base = GEO_ECPM_BASE[geo]
            fill_base = GEO_FILL_RATE_BASE[geo]

            for fmt in AD_FORMATS:
                imp = int(imp_base * FORMAT_IMPRESSIONS_SHARE[fmt] * np.random.uniform(0.85, 1.15))
                ecpm = ecpm_base * FORMAT_ECPM_MULT[fmt] * np.random.uniform(0.90, 1.10)
                fill = fill_base * FORMAT_FILL_MULT[fmt] * np.random.uniform(0.95, 1.05)
                fill = min(fill, 1.0)

                # --- Planted Anomalies ---

                # Anomaly 1: Day 45-47, US eCPM drops 40% (AdMob bidding issue)
                if 45 <= day_offset <= 47 and geo == "US" and channel == "AdMob":
                    ecpm *= 0.60

                # Anomaly 2: Day 60-61, IN fill_rate drops 30% (network outage)
                if 60 <= day_offset <= 61 and geo == "IN":
                    fill *= 0.70

                # Anomaly 3: Day 75, BR impressions spike +50% (promo campaign)
                if day_offset == 75 and geo == "BR":
                    imp = int(imp * 1.50)

                # Anomaly 4: Day 80, all geos drop 25% across all channels (market holiday)
                if day_offset == 80:
                    imp = int(imp * 0.75)

                revenue = imp * fill * ecpm / 1000
                clicks = int(imp * 0.02 * np.random.uniform(0.8, 1.2))

                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "channel": channel,
                    "geo": geo,
                    "ad_format": fmt,
                    "impressions": imp,
                    "clicks": max(clicks, 0),
                    "revenue": round(revenue, 2),
                    "ecpm": round(ecpm, 4),
                    "fill_rate": round(fill, 4),
                })

df = pd.DataFrame(records)
out = Path(__file__).parent / "sample_ad_revenue.csv"
df.to_csv(out, index=False)
print(f"Generated {len(df)} rows -> {out}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Total revenue: ${df['revenue'].sum():,.2f}")

# Quick anomaly check: expected revenue dips
d45_us = df[(df["date"].str.contains("2026-02-1[45]")) & (df["geo"] == "US")]["revenue"].sum()
print(f"Anomaly 1 (US day ~45): revenue around anomaly = ${d45_us:,.2f}")
