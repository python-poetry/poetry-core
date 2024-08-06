from __future__ import annotations

import pytest

from poetry.core.masonry.metadata import Metadata
from poetry.core.packages.project_package import ProjectPackage


@pytest.mark.parametrize(
    ("requires_python", "python", "expected"),
    [
        (">=3.8", None, ">=3.8"),
        (None, "^3.8", ">=3.8,<4.0"),
        (">=3.8", "^3.8", ">=3.8"),
    ],
)
def test_requires_python(
    requires_python: str | None, python: str | None, expected: str
) -> None:
    package = ProjectPackage("foo", "1")
    if requires_python:
        package.requires_python = requires_python
    if python:
        package.python_versions = python

    meta = Metadata.from_package(package)

    assert meta.requires_python == expected
