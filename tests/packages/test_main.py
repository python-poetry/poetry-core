from __future__ import annotations

from typing import cast

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.url_dependency import URLDependency
from poetry.core.packages.vcs_dependency import VCSDependency
from poetry.core.semver.version import Version


def test_dependency_from_pep_508() -> None:
    name = "requests"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == name
    assert str(dep.constraint) == "*"


def test_dependency_from_pep_508_with_version() -> None:
    name = "requests==2.18.0"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"


def test_dependency_from_pep_508_with_parens() -> None:
    name = "requests (==2.18.0)"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"


def test_dependency_from_pep_508_with_constraint() -> None:
    name = "requests>=2.12.0,!=2.17.*,<3.0"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == ">=2.12.0,<2.17.0 || >=2.18.0,<3.0"


def test_dependency_from_pep_508_with_extras() -> None:
    name = 'requests==2.18.0; extra == "foo" or extra == "bar"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.in_extras == ["foo", "bar"]
    assert str(dep.marker) == 'extra == "foo" or extra == "bar"'


def test_dependency_from_pep_508_with_python_version() -> None:
    name = 'requests (==2.18.0); python_version == "2.7" or python_version == "2.6"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "~2.7 || ~2.6"
    assert str(dep.marker) == 'python_version == "2.7" or python_version == "2.6"'


def test_dependency_from_pep_508_with_single_python_version() -> None:
    name = 'requests (==2.18.0); python_version == "2.7"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "~2.7"
    assert str(dep.marker) == 'python_version == "2.7"'


def test_dependency_from_pep_508_with_platform() -> None:
    name = 'requests (==2.18.0); sys_platform == "win32" or sys_platform == "darwin"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "*"
    assert str(dep.marker) == 'sys_platform == "win32" or sys_platform == "darwin"'


def test_dependency_from_pep_508_complex() -> None:
    name = (
        "requests (==2.18.0); "
        'python_version >= "2.7" and python_version != "3.2" '
        'and (sys_platform == "win32" or sys_platform == "darwin") '
        'and extra == "foo"'
    )
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.in_extras == ["foo"]
    assert dep.python_versions == ">=2.7 !=3.2.*"
    assert (
        str(dep.marker)
        == 'python_version >= "2.7" and python_version != "3.2" '
        'and (sys_platform == "win32" or sys_platform == "darwin") '
        'and extra == "foo"'
    )


def test_dependency_python_version_in() -> None:
    name = "requests (==2.18.0); python_version in '3.3 3.4 3.5'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.python_versions == "3.3.* || 3.4.* || 3.5.*"
    assert str(dep.marker) == 'python_version in "3.3 3.4 3.5"'


def test_dependency_python_version_in_comma() -> None:
    name = "requests (==2.18.0); python_version in '3.3, 3.4, 3.5'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.python_versions == "3.3.* || 3.4.* || 3.5.*"
    assert str(dep.marker) == 'python_version in "3.3, 3.4, 3.5"'


def test_dependency_platform_in() -> None:
    name = "requests (==2.18.0); sys_platform in 'win32 darwin'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert str(dep.marker) == 'sys_platform in "win32 darwin"'


def test_dependency_with_extra() -> None:
    name = "requests[security] (==2.18.0)"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"

    assert len(dep.extras) == 1
    assert "security" in dep.extras


def test_dependency_from_pep_508_with_python_version_union_of_multi() -> None:
    name = (
        "requests (==2.18.0); "
        '(python_version >= "2.7" and python_version < "2.8") '
        'or (python_version >= "3.4" and python_version < "3.5")'
    )
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == ">=2.7 <2.8 || >=3.4 <3.5"
    assert (
        str(dep.marker)
        == 'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "3.5"'
    )


def test_dependency_from_pep_508_with_not_in_op_marker() -> None:
    name = (
        'jinja2 (>=2.7,<2.8); python_version not in "3.0,3.1,3.2" and extra == "export"'
    )

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "jinja2"
    assert str(dep.constraint) == ">=2.7,<2.8"
    assert dep.in_extras == ["export"]
    assert dep.python_versions == "!=3.0.*, !=3.1.*, !=3.2.*"
    assert (
        str(dep.marker) == 'python_version not in "3.0,3.1,3.2" and extra == "export"'
    )


def test_dependency_from_pep_508_with_git_url() -> None:
    name = "django-utils @ git+ssh://git@corp-gitlab.com/corp-utils.git@1.2"

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "django-utils"
    assert dep.is_vcs()
    dep = cast(VCSDependency, dep)
    assert dep.vcs == "git"
    assert dep.source == "ssh://git@corp-gitlab.com/corp-utils.git"
    assert dep.reference == "1.2"


def test_dependency_from_pep_508_with_git_url_and_subdirectory() -> None:
    name = (
        "django-utils @"
        " git+ssh://git@corp-gitlab.com/corp-utils.git@1.2#subdirectory=package-dir"
    )

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "django-utils"
    assert dep.is_vcs()
    dep = cast(VCSDependency, dep)
    assert dep.vcs == "git"
    assert dep.source == "ssh://git@corp-gitlab.com/corp-utils.git"
    assert dep.reference == "1.2"
    assert dep.directory == "package-dir"


def test_dependency_from_pep_508_with_git_url_and_comment_and_extra() -> None:
    name = (
        "poetry @ git+https://github.com/python-poetry/poetry.git@b;ar;#egg=poetry"
        ' ; extra == "foo;"'
    )

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "poetry"
    assert dep.is_vcs()
    dep = cast(VCSDependency, dep)
    assert dep.vcs == "git"
    assert dep.source == "https://github.com/python-poetry/poetry.git"
    assert dep.reference == "b;ar;"
    assert dep.in_extras == ["foo;"]


def test_dependency_from_pep_508_with_url() -> None:
    name = "django-utils @ https://example.com/django-utils-1.0.0.tar.gz"

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "django-utils"
    assert dep.is_url()
    dep = cast(URLDependency, dep)
    assert dep.url == "https://example.com/django-utils-1.0.0.tar.gz"


def test_dependency_from_pep_508_with_wheel_url() -> None:
    name = (
        "example_wheel @ https://example.com/example_wheel-14.0.2-py2.py3-none-any.whl"
    )

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "example-wheel"
    assert str(dep.constraint) == "14.0.2"


def test_dependency_from_pep_508_with_python_full_version() -> None:
    name = (
        "requests (==2.18.0); "
        '(python_version >= "2.7" and python_version < "2.8") '
        'or (python_full_version >= "3.4" and python_full_version < "3.5.4")'
    )
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == ">=2.7 <2.8 || >=3.4 <3.5.4"
    assert (
        str(dep.marker)
        == 'python_version >= "2.7" and python_version < "2.8" '
        'or python_full_version >= "3.4" and python_full_version < "3.5.4"'
    )


def test_dependency_from_pep_508_with_python_full_version_pep440_compatible_release_astrix() -> None:
    name = 'pathlib2 ; python_version == "3.4.*" or python_version < "3"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "pathlib2"
    assert str(dep.constraint) == "*"
    assert dep.python_versions == "==3.4.* || <3"


def test_dependency_from_pep_508_with_python_full_version_pep440_compatible_release_tilde() -> None:
    name = 'pathlib2 ; python_version ~= "3.4" or python_version < "3"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "pathlib2"
    assert str(dep.constraint) == "*"
    assert dep.python_versions == "~=3.4 || <3"


def test_dependency_from_pep_508_should_not_produce_empty_constraints_for_correct_markers() -> None:
    name = (
        'pytest-mypy; python_implementation != "PyPy" and python_version <= "3.10" and'
        ' python_version > "3"'
    )
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "pytest-mypy"
    assert str(dep.constraint) == "*"
    assert dep.python_versions == "<=3.10 >3"
    assert dep.python_constraint.allows(Version.parse("3.6"))
    assert dep.python_constraint.allows(Version.parse("3.10"))
    assert not dep.python_constraint.allows(Version.parse("3"))
    assert dep.python_constraint.allows(Version.parse("3.0.1"))
    assert (
        str(dep.marker)
        == 'platform_python_implementation != "PyPy" and python_version <= "3.10" and'
        ' python_version > "3"'
    )
