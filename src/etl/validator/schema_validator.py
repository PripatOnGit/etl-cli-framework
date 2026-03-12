import json
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft7Validator


@dataclass
class ValidationResult:
    """Holds the result of validating one record."""

    record_index: int
    is_valid: bool
    errors: list[dict] = field(default_factory=list)


def load_schema(schema_path: str) -> dict:
    """Load JSON Schema from file."""
    with open(Path(schema_path), "r") as f:
        return json.load(f)


def validate_record(record: dict, schema: dict, index: int) -> ValidationResult:
    """
    Validate one record against schema.
    Collects ALL errors, not just the first one.
    """
    validator = Draft7Validator(schema)
    errors = []

    for error in validator.iter_errors(record):
        errors.append(
            {
                "field": list(error.path),
                "message": error.message,
                "value": error.instance,
                "rule": error.validator,
            }
        )

    return ValidationResult(
        record_index=index,
        is_valid=len(errors) == 0,
        errors=errors,
    )


def validate_batch(records: list[dict], schema: dict) -> tuple[list, list]:
    """
    Validate all records.
    Returns (valid_records, error_results).
    """
    valid = []
    errors = []

    for i, record in enumerate(records):
        result = validate_record(record, schema, i)
        if result.is_valid:
            valid.append(record)
        else:
            errors.append(result)

    return valid, errors
