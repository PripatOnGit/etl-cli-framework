import pytest

from etl.validator.schema_validator import (
    ValidationResult,
    validate_batch,
    validate_record,
)

SCHEMA = {
    "type": "object",
    "required": ["employee_id", "given_name", "salary", "hire_date"],
    "properties": {
        "employee_id": {"type": "string", "pattern": "^EMP[0-9]{4}$"},
        "given_name": {"type": "string", "minLength": 1},
        "salary": {"type": "number", "minimum": 0},
        "hire_date": {"type": "string"},
    },
}


# ── validate_record tests ─────────────────────────────────────────────────────


def test_valid_record_passes():
    record = {
        "employee_id": "EMP0001",
        "given_name": "Alice",
        "salary": 75000.0,
        "hire_date": "2022-01-15",
    }
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid is True
    assert result.errors == []


def test_invalid_employee_id_pattern_fails():
    record = {
        "employee_id": "BADID",
        "given_name": "Bob",
        "salary": 60000.0,
        "hire_date": "2022-03-10",
    }
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid is False
    fields = [e["field"][0] for e in result.errors if e["field"]]
    assert "employee_id" in fields


def test_negative_salary_fails():
    record = {
        "employee_id": "EMP0002",
        "given_name": "Carol",
        "salary": -500.0,
        "hire_date": "2022-05-01",
    }
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid is False
    fields = [e["field"][0] for e in result.errors if e["field"]]
    assert "salary" in fields


def test_missing_required_field_fails():
    record = {
        "employee_id": "EMP0003",
        "salary": 70000.0,
        "hire_date": "2022-07-20",
    }
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid is False


def test_multiple_errors_collected_in_one_pass():
    record = {
        "employee_id": "BADID",
        "given_name": "",
        "salary": -100.0,
        "hire_date": "2022-01-01",
    }
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid is False
    assert len(result.errors) >= 3


# ── validate_batch tests ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "record,expected_valid",
    [
        (
            {
                "employee_id": "EMP0001",
                "given_name": "Alice",
                "salary": 75000.0,
                "hire_date": "2022-01-15",
            },
            True,
        ),
        (
            {
                "employee_id": "BADID",
                "given_name": "Bob",
                "salary": 60000.0,
                "hire_date": "2022-03-10",
            },
            False,
        ),
        (
            {
                "employee_id": "EMP0002",
                "given_name": "",
                "salary": 60000.0,
                "hire_date": "2022-03-10",
            },
            False,
        ),
        (
            {
                "employee_id": "EMP0003",
                "given_name": "Carol",
                "salary": -1.0,
                "hire_date": "2022-05-01",
            },
            False,
        ),
    ],
)
def test_validate_record_parametrized(record, expected_valid):
    result = validate_record(record, SCHEMA, index=0)
    assert result.is_valid == expected_valid


def test_validate_batch_splits_correctly():
    valid_records = [
        {
            "employee_id": "EMP0001",
            "given_name": "Alice",
            "salary": 75000.0,
            "hire_date": "2022-01-15",
        },
        {
            "employee_id": "EMP0002",
            "given_name": "Bob",
            "salary": 60000.0,
            "hire_date": "2022-03-10",
        },
    ]
    invalid_records = [
        {
            "employee_id": "BADID",
            "given_name": "Carol",
            "salary": -500.0,
            "hire_date": "2022-05-01",
        },
        {
            "employee_id": "EMP0004",
            "given_name": "",
            "salary": 80000.0,
            "hire_date": "2022-07-20",
        },
    ]
    valid, errors = validate_batch(valid_records + invalid_records, SCHEMA)
    assert len(valid) == 2
    assert len(errors) == 2


def test_validate_batch_all_valid():
    records = [
        {
            "employee_id": "EMP0001",
            "given_name": "Alice",
            "salary": 75000.0,
            "hire_date": "2022-01-15",
        },
        {
            "employee_id": "EMP0002",
            "given_name": "Bob",
            "salary": 60000.0,
            "hire_date": "2022-03-10",
        },
    ]
    valid, errors = validate_batch(records, SCHEMA)
    assert len(valid) == 2
    assert len(errors) == 0


def test_validate_batch_all_invalid():
    records = [
        {"employee_id": "BAD1", "given_name": "", "salary": -1.0, "hire_date": "x"},
        {"employee_id": "BAD2", "given_name": "", "salary": -2.0, "hire_date": "x"},
    ]
    valid, errors = validate_batch(records, SCHEMA)
    assert len(valid) == 0
    assert len(errors) == 2
