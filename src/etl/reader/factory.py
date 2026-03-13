# src/etl/reader/factory.py
from __future__ import annotations

from .api_reader import ApiReader
from .base import BaseReader
from .csv_reader import CsvReader

_REGISTRY: dict[str, type[BaseReader]] = {
    "csv": CsvReader,
    "api": ApiReader,
}


def get_reader(config: dict) -> BaseReader:
    """Return the correct reader based on config['source']['type']."""
    source_type = config["source"]["type"]
    reader_class = _REGISTRY.get(source_type)
    if reader_class is None:
        supported = list(_REGISTRY.keys())
        raise ValueError(
            f"Unsupported source type: {source_type!r}. Supported: {supported}"
        )
    return reader_class(config)
