from __future__ import annotations

import os

from pathlib import Path
from stat import S_IREAD

import pytest

from poetry.core.utils.helpers import canonicalize_name
from poetry.core.utils.helpers import combine_unicode
from poetry.core.utils.helpers import normalize_version
from poetry.core.utils.helpers import parse_requires
from poetry.core.utils.helpers import readme_content_type
from poetry.core.utils.helpers import temporary_directory


@pytest.mark.parametrize(
    "version,normalized_version",
    [
        (  # already normalized version
            "1!2.3.4.5.6a7.post8.dev9+local1.123.abc",
            "1!2.3.4.5.6a7.post8.dev9+local1.123.abc",
        ),
        # PEP 440 Normalization
        # Case sensitivity
        ("1.1RC1", "1.1rc1"),
        # Integer Normalization
        ("00", "0"),
        ("09000", "9000"),
        ("1.0+foo0100", "1.0+foo0100"),
        # Pre-release separators
        ("1.1.a1", "1.1a1"),
        ("1.1-a1", "1.1a1"),
        ("1.1_a1", "1.1a1"),
        ("1.1a.1", "1.1a1"),
        ("1.1a-1", "1.1a1"),
        ("1.1a_1", "1.1a1"),
        # Pre-release spelling
        ("1.1alpha1", "1.1a1"),
        ("1.1beta2", "1.1b2"),
        ("1.1c3", "1.1rc3"),
        ("1.1pre4", "1.1rc4"),
        ("1.1preview5", "1.1rc5"),
        # Implicit pre-release number
        ("1.2a", "1.2a0"),
        # Post release separators
        ("1.2.post2", "1.2.post2"),
        ("1.2-post2", "1.2.post2"),
        ("1.2_post2", "1.2.post2"),
        ("1.2post.2", "1.2.post2"),
        ("1.2post-2", "1.2.post2"),
        ("1.2post_2", "1.2.post2"),
        # Post release spelling
        ("1.0-r4", "1.0.post4"),
        ("1.0-rev4", "1.0.post4"),
        # Implicit post release number
        ("1.2.post", "1.2.post0"),
        # Implicit post releases
        ("1.0-1", "1.0.post1"),
        # Development release separators
        ("1.2.dev2", "1.2.dev2"),
        ("1.2-dev2", "1.2.dev2"),
        ("1.2_dev2", "1.2.dev2"),
        ("1.2dev.2", "1.2.dev2"),
        ("1.2dev-2", "1.2.dev2"),
        ("1.2dev_2", "1.2.dev2"),
        # Implicit development release number
        ("1.2.dev", "1.2.dev0"),
        # Local version segments
        ("1.0+ubuntu-1", "1.0+ubuntu.1"),
        ("1.0+ubuntu_1", "1.0+ubuntu.1"),
        # Preceding v character
        ("v1.0", "1.0"),
        # Leading and Trailing Whitespace
        (" 1.0 ", "1.0"),
        ("\t1.0\t", "1.0"),
        ("\n1.0\n", "1.0"),
        ("\r\n1.0\r\n", "1.0"),
        ("\f1.0\f", "1.0"),
        ("\v1.0\v", "1.0"),
    ],
)
def test_normalize_version(version: str, normalized_version: str) -> None:
    assert normalize_version(version) == normalized_version


def test_parse_requires() -> None:
    requires = """\
jsonschema>=2.6.0.0,<3.0.0.0
lockfile>=0.12.0.0,<0.13.0.0
pip-tools>=1.11.0.0,<2.0.0.0
pkginfo>=1.4.0.0,<2.0.0.0
pyrsistent>=0.14.2.0,<0.15.0.0
toml>=0.9.0.0,<0.10.0.0
cleo>=0.6.0.0,<0.7.0.0
cachy>=0.1.1.0,<0.2.0.0
cachecontrol>=0.12.4.0,<0.13.0.0
requests>=2.18.0.0,<3.0.0.0
msgpack-python>=0.5.0.0,<0.6.0.0
pyparsing>=2.2.0.0,<3.0.0.0
requests-toolbelt>=0.8.0.0,<0.9.0.0

[:(python_version >= "2.7.0.0" and python_version < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")]
typing>=3.6.0.0,<4.0.0.0

[:python_version >= "2.7.0.0" and python_version < "2.8.0.0"]
virtualenv>=15.2.0.0,<16.0.0.0
pathlib2>=2.3.0.0,<3.0.0.0

[:python_version >= "3.4.0.0" and python_version < "3.6.0.0"]
zipfile36>=0.1.0.0,<0.2.0.0

[dev]
isort@ git+git://github.com/timothycrosley/isort.git@e63ae06ec7d70b06df9e528357650281a3d3ec22#egg=isort
"""
    result = parse_requires(requires)
    expected = [
        "jsonschema>=2.6.0.0,<3.0.0.0",
        "lockfile>=0.12.0.0,<0.13.0.0",
        "pip-tools>=1.11.0.0,<2.0.0.0",
        "pkginfo>=1.4.0.0,<2.0.0.0",
        "pyrsistent>=0.14.2.0,<0.15.0.0",
        "toml>=0.9.0.0,<0.10.0.0",
        "cleo>=0.6.0.0,<0.7.0.0",
        "cachy>=0.1.1.0,<0.2.0.0",
        "cachecontrol>=0.12.4.0,<0.13.0.0",
        "requests>=2.18.0.0,<3.0.0.0",
        "msgpack-python>=0.5.0.0,<0.6.0.0",
        "pyparsing>=2.2.0.0,<3.0.0.0",
        "requests-toolbelt>=0.8.0.0,<0.9.0.0",
        'typing>=3.6.0.0,<4.0.0.0 ; (python_version >= "2.7.0.0" and python_version <'
        ' "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")',
        'virtualenv>=15.2.0.0,<16.0.0.0 ; python_version >= "2.7.0.0" and'
        ' python_version < "2.8.0.0"',
        'pathlib2>=2.3.0.0,<3.0.0.0 ; python_version >= "2.7.0.0" and python_version <'
        ' "2.8.0.0"',
        'zipfile36>=0.1.0.0,<0.2.0.0 ; python_version >= "3.4.0.0" and python_version <'
        ' "3.6.0.0"',
        "isort@"
        " git+git://github.com/timothycrosley/isort.git@e63ae06ec7d70b06df9e528357650281a3d3ec22#egg=isort"
        ' ; extra == "dev"',
    ]
    assert result == expected


@pytest.mark.parametrize("raw", ["a-b-c", "a_b-c", "a_b_c", "a-b_c", "a.b-c"])
def test_utils_helpers_canonical_names(raw: str) -> None:
    assert canonicalize_name(raw) == "a-b-c"


def test_utils_helpers_combine_unicode() -> None:
    combined_expected = "é"
    decomposed = "é"
    assert combined_expected != decomposed

    combined = combine_unicode(decomposed)
    assert combined == combined_expected


def test_utils_helpers_temporary_directory_readonly_file() -> None:
    with temporary_directory() as temp_dir:
        readonly_filename = os.path.join(temp_dir, "file.txt")
        with open(readonly_filename, "w+") as readonly_file:
            readonly_file.write("Poetry rocks!")
        os.chmod(str(readonly_filename), S_IREAD)

    assert not os.path.exists(temp_dir)
    assert not os.path.exists(readonly_filename)


@pytest.mark.parametrize(
    "readme, content_type",
    [
        ("README.rst", "text/x-rst"),
        ("README.md", "text/markdown"),
        ("README", "text/plain"),
        (Path("README.rst"), "text/x-rst"),
        (Path("README.md"), "text/markdown"),
        (Path("README"), "text/plain"),
    ],
)
def test_utils_helpers_readme_content_type(
    readme: str | Path, content_type: str
) -> None:
    assert readme_content_type(readme) == content_type
