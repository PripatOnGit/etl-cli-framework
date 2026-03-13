# src/etl/reader/base.py
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseReader(ABC):
    """All readers must implement read() and return a DataFrame."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def read(self) -> pd.DataFrame:
        """Read data and return as a DataFrame."""
        ...
