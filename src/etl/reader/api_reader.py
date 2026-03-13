# src/etl/reader/api_reader.py
from __future__ import annotations

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseReader


class ApiReader(BaseReader):
    """Reads JSON data from a REST API with automatic retry."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _fetch(self, url: str, headers: dict) -> list[dict]:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def read(self) -> pd.DataFrame:
        url = self.config["source"]["url"]
        headers = self.config["source"].get("headers", {})
        data = self._fetch(url, headers)
        return pd.json_normalize(data)
