from __future__ import annotations

from typing import Any

import pytest

from poetry.core.json import validate_object


@pytest.fixture
def base_object() -> dict[str, Any]:
    return {
        "name": "myapp",
        "version": "1.0.0",
        "description": "Some description.",
        "dependencies": {"python": "^3.6"},
        "dev-dependencies": {},
    }


@pytest.fixture
def multi_url_object() -> dict[str, Any]:
    return {
        "name": "myapp",
        "version": "1.0.0",
        "description": "Some description.",
        "dependencies": {
            "python": [
                {
                    "url": "https://download.pytorch.org/whl/cpu/torch-1.4.0%2Bcpu-cp37-cp37m-linux_x86_64.whl",
                    "platform": "linux",
                },
                {"path": "../foo", "platform": "darwin"},
            ]
        },
        "dev-dependencies": {},
    }


def test_path_dependencies(base_object: dict[str, Any]) -> None:
    base_object["dependencies"].update({"foo": {"path": "../foo"}})
    base_object["dev-dependencies"].update({"foo": {"path": "../foo"}})

    assert len(validate_object(base_object, "poetry-schema")) == 0


def test_multi_url_dependencies(multi_url_object: dict[str, Any]) -> None:
    assert len(validate_object(multi_url_object, "poetry-schema")) == 0


def test_multiline_description(base_object: dict[str, Any]) -> None:
    bad_description = "Some multi-\nline string"
    base_object["description"] = bad_description

    errors = validate_object(base_object, "poetry-schema")
    assert len(errors) == 1
    assert errors[0] == f"[description] {bad_description!r} does not match '^[^\\n]*$'"
