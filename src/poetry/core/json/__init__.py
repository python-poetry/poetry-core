from __future__ import annotations

import json

from pathlib import Path
import sys
from typing import Any

if sys.version_info[:2] < (3, 9):
    import importlib_resources
else:
    from importlib import resources as importlib_resources

import fastjsonschema

from fastjsonschema.exceptions import JsonSchemaException


SCHEMA_DIR = Path(__file__).parent / "schemas"


class ValidationError(ValueError):
    pass


def validate_object(obj: dict[str, Any], schema_name: str) -> list[str]:
    schema_file = (
        importlib_resources.files("poetry.core.json").joinpath("schemas")
        / f"{schema_name}.json"
    )

    if not schema_file.is_file():
        raise ValueError(f"Schema {schema_name} does not exist.")

    with schema_file.open(encoding="utf-8") as f:
        schema = json.load(f)

    validate = fastjsonschema.compile(schema)

    errors = []
    try:
        validate(obj)
    except JsonSchemaException as e:
        errors = [e.message]

    return errors
