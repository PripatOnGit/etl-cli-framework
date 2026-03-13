# src/etl/reader/csv_reader.py
from __future__ import annotations

import pandas as pd

from .base import BaseReader


class CsvReader(BaseReader):
    """Reads a CSV file into a DataFrame."""

    def read(self) -> pd.DataFrame:
        path = self.config["source"]["path"]
        encoding = self.config["source"].get("encoding", "utf-8")
        return pd.read_csv(
            path,
            dtype=str,  # read everything as string first
            keep_default_na=False,  # don't convert 'NA', 'None' etc to NaN
            encoding=encoding,
        )
