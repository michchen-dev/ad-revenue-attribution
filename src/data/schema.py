"""Ad revenue data schema: expected columns, types, and validation rules."""

EXPECTED_COLUMNS = {
    "date": "datetime64[ns]",
    "channel": "object",
    "geo": "object",
    "ad_format": "object",
    "impressions": "int64",
    "clicks": "int64",
    "revenue": "float64",
    "ecpm": "float64",
    "fill_rate": "float64",
}

DIMENSION_COLUMNS = ["channel", "geo", "ad_format"]
METRIC_COLUMNS = ["impressions", "clicks", "revenue", "ecpm", "fill_rate"]
ALL_COLUMNS = ["date"] + DIMENSION_COLUMNS + METRIC_COLUMNS

REQUIRED_COLUMNS = ["date", "channel", "geo", "impressions", "revenue", "ecpm", "fill_rate"]
OPTIONAL_COLUMNS = ["ad_format", "clicks"]
