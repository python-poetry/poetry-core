import os

from stat import S_IREAD

import pytest

from poetry.core.utils.helpers import canonicalize_name
from poetry.core.utils.helpers import parse_requires
from poetry.core.utils.helpers import temporary_directory


def test_parse_requires():
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
        'typing>=3.6.0.0,<4.0.0.0 ; (python_version >= "2.7.0.0" and python_version < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")',
        'virtualenv>=15.2.0.0,<16.0.0.0 ; python_version >= "2.7.0.0" and python_version < "2.8.0.0"',
        'pathlib2>=2.3.0.0,<3.0.0.0 ; python_version >= "2.7.0.0" and python_version < "2.8.0.0"',
        'zipfile36>=0.1.0.0,<0.2.0.0 ; python_version >= "3.4.0.0" and python_version < "3.6.0.0"',
        'isort@ git+git://github.com/timothycrosley/isort.git@e63ae06ec7d70b06df9e528357650281a3d3ec22#egg=isort ; extra == "dev"',
    ]
    assert result == expected


@pytest.mark.parametrize("raw", ["a-b-c", "a_b-c", "a_b_c", "a-b_c"])
def test_utils_helpers_canonical_names(raw):
    assert canonicalize_name(raw) == "a-b-c"


def test_utils_helpers_temporary_directory_readonly_file():
    with temporary_directory() as temp_dir:
        readonly_filename = os.path.join(temp_dir, "file.txt")
        with open(readonly_filename, "w+") as readonly_file:
            readonly_file.write("Poetry rocks!")
        os.chmod(str(readonly_filename), S_IREAD)

    assert not os.path.exists(temp_dir)
    assert not os.path.exists(readonly_filename)
