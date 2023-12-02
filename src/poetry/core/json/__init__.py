from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import fastjsonschema

from fastjsonschema.exceptions import JsonSchemaException

from poetry.core.json import schemas
from poetry.core.utils._compat import importlib_resources


# TODO: Remove this?
SCHEMA_DIR = Path(__file__).parent / "schemas"


class ValidationError(ValueError):
    pass


def validate_object(obj: dict[str, Any], schema_name: str) -> list[str]:
    schema_file = importlib_resources.files(schemas).joinpath(f"{schema_name}.json")

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
