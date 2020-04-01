# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from poetry.core.packages import Package


def test_package_authors():
    package = Package("foo", "0.1.0")

    package.authors.append("Sébastien Eustace <sebastien@eustace.io>")
    assert package.author_name == "Sébastien Eustace"
    assert package.author_email == "sebastien@eustace.io"

    package.authors.insert(0, "John Doe")
    assert package.author_name == "John Doe"
    assert package.author_email is None


@pytest.mark.parametrize("category", ["main", "dev"])
def test_package_add_dependency_vcs_category(category):
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        "poetry",
        constraint={"git": "https://github.com/python-poetry/poetry.git"},
        category=category,
    )
    assert dependency.category == category


def test_package_add_dependency_vcs_category_default_main():
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        "poetry", constraint={"git": "https://github.com/python-poetry/poetry.git"}
    )
    assert dependency.category == "main"


@pytest.mark.parametrize("category", ["main", "dev"])
@pytest.mark.parametrize("optional", [True, False])
def test_package_url_category_optional(category, optional):
    package = Package("foo", "0.1.0")

    dependency = package.add_dependency(
        "poetry",
        constraint={
            "url": "https://github.com/python-poetry/poetry/releases/download/1.0.5/poetry-1.0.5-linux.tar.gz",
            "optional": optional,
        },
        category=category,
    )
    assert dependency.category == category
    assert dependency.is_optional() == optional
