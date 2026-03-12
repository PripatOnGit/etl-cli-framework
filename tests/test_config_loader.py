import pytest

from etl.config_loader import (
    ConfigError,
    get_filters,
    get_rename_map,
    get_type_casts,
    load_config,
)


def test_load_valid_config(tmp_path):
    config_file = tmp_path / "pipeline.yaml"
    config_file.write_text(
        "source:\n  type: csv\n"
        "target:\n  type: sqlite\n"
        "transformations:\n  rename_columns: {}\n"
        "validation:\n  schema_file: schema.json\n"
    )
    config = load_config(str(config_file))
    assert config["source"]["type"] == "csv"


def test_missing_config_file_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/path.yaml")


def test_missing_required_key_raises(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("source:\n  type: csv\n")
    with pytest.raises(ConfigError, match="Missing required"):
        load_config(str(config_file))


def test_get_rename_map_returns_correct_values():
    config = {"transformations": {"rename_columns": {"first_name": "given_name"}}}
    result = get_rename_map(config)
    assert result == {"first_name": "given_name"}


def test_get_rename_map_returns_empty_when_missing():
    config = {"transformations": {}}
    result = get_rename_map(config)
    assert result == {}


def test_get_filters_returns_correct_values():
    config = {
        "transformations": {
            "filters": [{"column": "age", "operator": "gte", "value": 18}]
        }
    }
    result = get_filters(config)
    assert len(result) == 1
    assert result[0]["column"] == "age"


def test_get_type_casts_returns_correct_values():
    config = {"transformations": {"type_casts": {"salary": "float"}}}
    result = get_type_casts(config)
    assert result == {"salary": "float"}
