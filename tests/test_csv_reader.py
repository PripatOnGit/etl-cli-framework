import pandas as pd
import pytest

from etl.reader.csv_reader import CsvReader


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("id,name,age\n1,Alice,30\n2,Bob,25\n")
    return f


def test_reads_csv(csv_file):
    config = {"source": {"path": str(csv_file)}}
    df = CsvReader(config).read()
    assert len(df) == 2
    assert list(df.columns) == ["id", "name", "age"]


def test_all_columns_are_strings(csv_file):
    """dtype=str means even numeric columns come back as strings."""
    config = {"source": {"path": str(csv_file)}}
    df = CsvReader(config).read()
    assert pd.api.types.is_string_dtype(df["age"])


def test_file_not_found():
    config = {"source": {"path": "/nonexistent/file.csv"}}
    with pytest.raises(FileNotFoundError):
        CsvReader(config).read()
