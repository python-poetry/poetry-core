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
        "authors": ["Your Name <you@example.com>"],
        "dependencies": {"python": "^3.6"},
        "group": {"dev": {"dependencies": {}}},
    }


@pytest.fixture
def multi_url_object() -> dict[str, Any]:
    return {
        "name": "myapp",
        "version": "1.0.0",
        "description": "Some description.",
        "authors": ["Your Name <you@example.com>"],
        "dependencies": {
            "python": [
                {
                    "url": "https://download.pytorch.org/whl/cpu/torch-1.4.0%2Bcpu-cp37-cp37m-linux_x86_64.whl",
                    "platform": "linux",
                },
                {"path": "../foo", "platform": "darwin"},
            ]
        },
    }


def test_non_package_mode_no_metadata() -> None:
    assert len(validate_object({"package-mode": False}, "poetry-schema")) == 0


def test_non_package_mode_with_metadata(base_object: dict[str, Any]) -> None:
    base_object["package-mode"] = False
    assert len(validate_object(base_object, "poetry-schema")) == 0


def test_invalid_mode() -> None:
    assert len(validate_object({"package-mode": "foo"}, "poetry-schema")) == 1


def test_path_dependencies(base_object: dict[str, Any]) -> None:
    base_object["dependencies"].update({"foo": {"path": "../foo"}})
    base_object["group"]["dev"]["dependencies"].update({"foo": {"path": "../foo"}})

    assert len(validate_object(base_object, "poetry-schema")) == 0


def test_multi_url_dependencies(multi_url_object: dict[str, Any]) -> None:
    assert len(validate_object(multi_url_object, "poetry-schema")) == 0


@pytest.mark.parametrize(
    "git",
    [
        "https://github.com/example/example-repository.git",
        "git@github.com:example/example-repository.git",
    ],
)
def test_git_dependencies(base_object: dict[str, Any], git: str) -> None:
    base_object["dependencies"].update({"git-dependency": {"git": git}})

    assert len(validate_object(base_object, "poetry-schema")) == 0


@pytest.mark.parametrize(
    "bad_description",
    ["Some multi-\nline string", "Some multiline string\n", "\nSome multi-line string"],
)
def test_multiline_description(
    base_object: dict[str, Any], bad_description: str
) -> None:
    base_object["description"] = bad_description

    errors = validate_object(base_object, "poetry-schema")

    assert len(errors) == 1

    regex = r"\A[^\n]*\Z"
    assert errors[0] == f"data.description must match pattern {regex}"


def test_bad_extra(base_object: dict[str, Any]) -> None:
    bad_extra = "a{[*+"
    base_object["extras"] = {}
    base_object["extras"]["test"] = [bad_extra]

    errors = validate_object(base_object, "poetry-schema")
    assert len(errors) == 1
    assert errors[0] == "data.extras.test[0] must match pattern ^[a-zA-Z-_.0-9]+$"
