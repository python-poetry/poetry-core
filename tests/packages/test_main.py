from poetry.core.packages.dependency import Dependency
from poetry.core.semver.version import Version


def test_dependency_from_pep_508():
    name = "requests"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == name
    assert str(dep.constraint) == "*"


def test_dependency_from_pep_508_with_version():
    name = "requests==2.18.0"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"


def test_dependency_from_pep_508_with_parens():
    name = "requests (==2.18.0)"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"


def test_dependency_from_pep_508_with_constraint():
    name = "requests>=2.12.0,!=2.17.*,<3.0"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == ">=2.12.0,<2.17.0 || >=2.18.0,<3.0"


def test_dependency_from_pep_508_with_extras():
    name = 'requests==2.18.0; extra == "foo" or extra == "bar"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.in_extras == ["foo", "bar"]
    assert str(dep.marker) == 'extra == "foo" or extra == "bar"'


def test_dependency_from_pep_508_with_python_version():
    name = 'requests (==2.18.0); python_version == "2.7" or python_version == "2.6"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "~2.7 || ~2.6"
    assert str(dep.marker) == 'python_version == "2.7" or python_version == "2.6"'


def test_dependency_from_pep_508_with_single_python_version():
    name = 'requests (==2.18.0); python_version == "2.7"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "~2.7"
    assert str(dep.marker) == 'python_version == "2.7"'


def test_dependency_from_pep_508_with_platform():
    name = 'requests (==2.18.0); sys_platform == "win32" or sys_platform == "darwin"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.extras == frozenset()
    assert dep.python_versions == "*"
    assert str(dep.marker) == 'sys_platform == "win32" or sys_platform == "darwin"'


def test_dependency_from_pep_508_complex():
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
    assert str(dep.marker) == (
        'python_version >= "2.7" and python_version != "3.2" '
        'and (sys_platform == "win32" or sys_platform == "darwin") '
        'and extra == "foo"'
    )


def test_dependency_python_version_in():
    name = "requests (==2.18.0); python_version in '3.3 3.4 3.5'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.python_versions == "3.3.* || 3.4.* || 3.5.*"
    assert str(dep.marker) == 'python_version in "3.3 3.4 3.5"'


def test_dependency_python_version_in_comma():
    name = "requests (==2.18.0); python_version in '3.3, 3.4, 3.5'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert dep.python_versions == "3.3.* || 3.4.* || 3.5.*"
    assert str(dep.marker) == 'python_version in "3.3, 3.4, 3.5"'


def test_dependency_platform_in():
    name = "requests (==2.18.0); sys_platform in 'win32 darwin'"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"
    assert str(dep.marker) == 'sys_platform in "win32 darwin"'


def test_dependency_with_extra():
    name = "requests[security] (==2.18.0)"
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "requests"
    assert str(dep.constraint) == "2.18.0"

    assert len(dep.extras) == 1
    assert "security" in dep.extras


def test_dependency_from_pep_508_with_python_version_union_of_multi():
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
    assert str(dep.marker) == (
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_version >= "3.4" and python_version < "3.5"'
    )


def test_dependency_from_pep_508_with_not_in_op_marker():
    name = (
        "jinja2 (>=2.7,<2.8)"
        '; python_version not in "3.0,3.1,3.2" and extra == "export"'
    )

    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "jinja2"
    assert str(dep.constraint) == ">=2.7,<2.8"
    assert dep.in_extras == ["export"]
    assert dep.python_versions == "!=3.0.*, !=3.1.*, !=3.2.*"
    assert (
        str(dep.marker) == 'python_version not in "3.0,3.1,3.2" and extra == "export"'
    )


def test_dependency_from_pep_508_with_git_url():
    name = "django-utils @ git+ssh://git@corp-gitlab.com/corp-utils.git@1.2"

    dep = Dependency.create_from_pep_508(name)

    assert "django-utils" == dep.name
    assert dep.is_vcs()
    assert "git" == dep.vcs
    assert "ssh://git@corp-gitlab.com/corp-utils.git" == dep.source
    assert "1.2" == dep.reference


def test_dependency_from_pep_508_with_git_url_and_comment_and_extra():
    name = (
        "poetry @ git+https://github.com/python-poetry/poetry.git@b;ar;#egg=poetry"
        ' ; extra == "foo;"'
    )

    dep = Dependency.create_from_pep_508(name)

    assert "poetry" == dep.name
    assert dep.is_vcs()
    assert "git" == dep.vcs
    assert "https://github.com/python-poetry/poetry.git" == dep.source
    assert "b;ar;" == dep.reference
    assert dep.in_extras == ["foo;"]


def test_dependency_from_pep_508_with_url():
    name = "django-utils @ https://example.com/django-utils-1.0.0.tar.gz"

    dep = Dependency.create_from_pep_508(name)

    assert "django-utils" == dep.name
    assert dep.is_url()
    assert "https://example.com/django-utils-1.0.0.tar.gz" == dep.url


def test_dependency_from_pep_508_with_wheel_url():
    name = (
        "example_wheel @ https://example.com/example_wheel-14.0.2-py2.py3-none-any.whl"
    )

    dep = Dependency.create_from_pep_508(name)

    assert "example-wheel" == dep.name
    assert str(dep.constraint) == "14.0.2"


def test_dependency_from_pep_508_with_python_full_version():
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
    assert str(dep.marker) == (
        'python_version >= "2.7" and python_version < "2.8" '
        'or python_full_version >= "3.4" and python_full_version < "3.5.4"'
    )


def test_dependency_from_pep_508_with_python_full_version_pep440_compatible_release_astrix():
    name = 'pathlib2 ; python_version == "3.4.*" or python_version < "3"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "pathlib2"
    assert str(dep.constraint) == "*"
    assert dep.python_versions == "==3.4.* || <3"


def test_dependency_from_pep_508_with_python_full_version_pep440_compatible_release_tilde():
    name = 'pathlib2 ; python_version ~= "3.4" or python_version < "3"'
    dep = Dependency.create_from_pep_508(name)

    assert dep.name == "pathlib2"
    assert str(dep.constraint) == "*"
    assert dep.python_versions == "~=3.4 || <3"


def test_dependency_from_pep_508_should_not_produce_empty_constraints_for_correct_markers():
    name = 'pytest-mypy; python_implementation != "PyPy" and python_version <= "3.10" and python_version > "3"'
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
        == 'platform_python_implementation != "PyPy" and python_version <= "3.10" and python_version > "3"'
    )
