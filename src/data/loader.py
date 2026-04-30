"""CSV/Excel data loader with schema validation."""

import pandas as pd
from pathlib import Path
from src.data.schema import EXPECTED_COLUMNS, REQUIRED_COLUMNS, DIMENSION_COLUMNS


class DataLoader:
    def __init__(self):
        self.df = None
        self.errors = []

    def load(self, file) -> pd.DataFrame:
        self.errors = []
        path = Path(file.name) if hasattr(file, "name") else Path(file)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            self.df = pd.read_csv(file)
        elif suffix in (".xlsx", ".xls"):
            self.df = pd.read_excel(file)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}，请上传 CSV 或 Excel 文件")

        self._validate()
        self._transform()
        return self.df

    def _validate(self):
        missing = [c for c in REQUIRED_COLUMNS if c not in self.df.columns]
        if missing:
            self.errors.append(f"缺少必要列: {', '.join(missing)}")

        extra = [c for c in DIMENSION_COLUMNS if c not in self.df.columns]
        if extra and extra != DIMENSION_COLUMNS:
            self.errors.append(f"警告: 缺少维度列 {', '.join(extra)}，归因分析粒度将受限")

        if "revenue" in self.df.columns and (self.df["revenue"] < 0).any():
            self.errors.append("警告: revenue 列包含负值")

    def _transform(self):
        if "date" in self.df.columns:
            self.df["date"] = pd.to_datetime(self.df["date"])

        for dim in DIMENSION_COLUMNS:
            if dim in self.df.columns:
                self.df[dim] = self.df[dim].astype(str)

        if "revenue" in self.df.columns and "impressions" in self.df.columns:
            if "ecpm" not in self.df.columns or self.df["ecpm"].isna().all():
                self.df["ecpm"] = (self.df["revenue"] / self.df["impressions"] * 1000).round(4)
                self.df["ecpm"] = self.df["ecpm"].replace([float("inf"), float("-inf")], 0)

        self.df = self.df.sort_values("date").reset_index(drop=True)

    def is_valid(self) -> bool:
        return len([e for e in self.errors if "缺少" in e]) == 0
