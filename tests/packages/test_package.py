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


def test_package_authors_invalid():
    package = Package("foo", "0.1.0")

    package.authors.insert(0, "<John Doe")
    with pytest.raises(ValueError) as e:
        package.author_name

    assert (
        str(e.value)
        == "Invalid author string. Must be in the format: John Smith <john@example.com>"
    )


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


def test_package_equality_simple():
    assert Package("foo", "0.1.0") == Package("foo", "0.1.0")
    assert Package("foo", "0.1.0") != Package("foo", "0.1.1")
    assert Package("bar", "0.1.0") != Package("foo", "0.1.0")


def test_package_equality_source_type():
    a1 = Package("a", "0.1.0")
    a1.source_type = "file"

    a2 = Package(a1.name, a1.version)
    a2.source_type = "directory"

    a3 = Package(a1.name, a1.version)
    a3.source_type = a1.source_type

    a4 = Package(a1.name, a1.version)

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_package_equality_source_url():
    a1 = Package("a", "0.1.0")
    a1.source_type = "file"
    a1.source_url = "/some/path"

    a2 = Package(a1.name, a1.version)
    a2.source_type = a1.source_type
    a2.source_url = "/some/other/path"

    a3 = Package(a1.name, a1.version)
    a3.source_type = a1.source_type
    a3.source_url = a1.source_url

    a4 = Package(a1.name, a1.version)
    a4.source_type = a1.source_type

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4


def test_package_equality_source_reference():
    a1 = Package("a", "0.1.0")
    a1.source_type = "git"
    a1.source_reference = "c01b317af582501c5ba07b23d5bef3fbada2d4ef"

    a2 = Package(a1.name, a1.version)
    a2.source_type = a1.source_type
    a2.source_reference = "a444731cd243cb5cd04e4d5fb81f86e1fecf8a00"

    a3 = Package(a1.name, a1.version)
    a3.source_type = a1.source_type
    a3.source_reference = a1.source_reference

    a4 = Package(a1.name, a1.version)
    a4.source_type = a1.source_type

    assert a1 == a1
    assert a1 == a3
    assert a1 != a2
    assert a2 != a3
    assert a1 != a4
    assert a2 != a4
