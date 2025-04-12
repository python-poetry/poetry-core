from __future__ import annotations

from pathlib import Path

import pytest

from packaging.utils import canonicalize_name

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.dependency_group import DependencyGroup
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.vcs_dependency import VCSDependency


def create_dependency(
    name: str,
    constraint: str = "*",
    *,
    optional: bool = False,
    extras: tuple[str, ...] = (),
    in_extras: tuple[str, ...] = (),
    allows_prereleases: bool | None = None,
    develop: bool = False,
    source_name: str | None = None,
    marker: str | None = None,
) -> Dependency:
    dep = Dependency(
        name=name,
        constraint=constraint,
        optional=optional,
        extras=extras,
        allows_prereleases=allows_prereleases,
    )
    if in_extras:
        dep._optional = True
        dep._in_extras = [canonicalize_name(extra) for extra in in_extras]
    if develop:
        dep._develop = develop
    if source_name:
        dep.source_name = source_name
    if marker:
        dep.marker = marker  # type: ignore[assignment]
    return dep


@pytest.mark.parametrize("mixed_dynamic", [False, True])
@pytest.mark.parametrize(
    (
        "dependencies",
        "poetry_dependencies",
        "expected_dependencies",
    ),
    [
        ({Dependency("foo", "*", optional=True)}, set(), {"foo"}),
        (set(), {Dependency("bar", "*")}, {"bar"}),
        (set(), {Dependency("bar", "*", optional=True)}, {"bar"}),
        ({Dependency("foo", "*")}, {Dependency("bar", "*")}, {"foo"}),
        (
            {Dependency("foo", "*", optional=True)},
            {Dependency("bar", "*")},
            ({"foo"}, {"foo", "bar"}),
        ),
        (
            {Dependency("foo", "*")},
            {Dependency("bar", "*", optional=True)},
            ({"foo"}, {"foo", "bar"}),
        ),
        (
            {
                Dependency("foo", "*", optional=True),
                Dependency("baz", "*", optional=True),
            },
            {Dependency("bar", "*")},
            ({"foo", "baz"}, {"foo", "bar", "baz"}),
        ),
        (
            {
                Dependency("foo", "*", optional=True),
                Dependency("baz", "*", optional=False),
            },
            {Dependency("bar", "*")},
            {"foo", "baz"},
        ),
        (
            {Dependency("foo", "*", optional=True)},
            {Dependency("bar", "*"), Dependency("baz", "*", optional=True)},
            ({"foo"}, {"foo", "bar"}),
        ),
    ],
)
def test_dependencies(
    dependencies: set[Dependency],
    poetry_dependencies: set[Dependency],
    mixed_dynamic: bool,
    expected_dependencies: set[str] | tuple[set[str], set[str]],
) -> None:
    group = DependencyGroup(name="group", mixed_dynamic=mixed_dynamic)
    group._dependencies = list(dependencies)
    group._poetry_dependencies = list(poetry_dependencies)

    if isinstance(expected_dependencies, tuple):
        expected_dependencies = (
            expected_dependencies[1] if mixed_dynamic else expected_dependencies[0]
        )
    assert {d.name for d in group.dependencies} == expected_dependencies


@pytest.mark.parametrize(
    (
        "initial_dependencies",
        "initial_poetry_dependencies",
        "expected_dependencies",
        "expected_poetry_dependencies",
    ),
    [
        (set(), set(), {"new"}, set()),
        ({"foo"}, set(), {"foo", "new"}, set()),
        (set(), {"bar"}, set(), {"bar", "new"}),
        ({"foo"}, {"bar"}, {"foo", "new"}, {"bar"}),
    ],
)
def test_add_dependency_adds_to_correct_list(
    initial_dependencies: set[str],
    initial_poetry_dependencies: set[str],
    expected_dependencies: set[str],
    expected_poetry_dependencies: set[str],
) -> None:
    group = DependencyGroup(name="group")
    group._dependencies = [
        Dependency(name=name, constraint="*") for name in initial_dependencies
    ]
    group._poetry_dependencies = [
        Dependency(name=name, constraint="*") for name in initial_poetry_dependencies
    ]

    group.add_dependency(Dependency(name="new", constraint="*"))

    assert {d.name for d in group._dependencies} == expected_dependencies
    assert {d.name for d in group._poetry_dependencies} == expected_poetry_dependencies


def test_remove_dependency_removes_from_both_lists() -> None:
    group = DependencyGroup(name="group")
    group.add_dependency(Dependency(name="foo", constraint="*"))
    group.add_dependency(Dependency(name="bar", constraint="*"))
    group.add_dependency(Dependency(name="foo", constraint="*"))
    group.add_poetry_dependency(Dependency(name="baz", constraint="*"))
    group.add_poetry_dependency(Dependency(name="foo", constraint="*"))

    group.remove_dependency("foo")

    assert {d.name for d in group._dependencies} == {"bar"}
    assert {d.name for d in group._poetry_dependencies} == {"baz"}


@pytest.mark.parametrize("mixed_dynamic", [False, True])
@pytest.mark.parametrize(
    (
        "dependencies",
        "poetry_dependencies",
        "expected_dependencies",
    ),
    [
        ([Dependency.create_from_pep_508("foo")], [], [create_dependency("foo")]),
        ([], [Dependency.create_from_pep_508("bar")], [create_dependency("bar")]),
        (
            [create_dependency("foo")],
            [create_dependency("bar")],
            [create_dependency("foo")],
        ),
        (
            [create_dependency("foo", in_extras=("extra1",))],
            [create_dependency("bar")],
            (
                [create_dependency("foo", in_extras=("extra1",))],
                [
                    create_dependency("foo", in_extras=("extra1",)),
                    create_dependency("bar"),
                ],
            ),
        ),
        (
            [create_dependency("foo")],
            [create_dependency("bar", in_extras=("extra1",))],
            (
                [create_dependency("foo")],
                [
                    create_dependency("foo"),
                    create_dependency("bar", in_extras=("extra1",)),
                ],
            ),
        ),
        # refine constraint
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", "<2")],
            [create_dependency("foo", ">=1,<2")],
        ),
        # refine constraint + other dependency
        (
            [
                Dependency.create_from_pep_508("foo>=1"),
                Dependency.create_from_pep_508("bar>=2"),
            ],
            [create_dependency("foo", "<2")],
            [create_dependency("foo", ">=1,<2"), create_dependency("bar", ">=2")],
        ),
        # refine constraint depending on marker
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", "<2", marker="sys_platform == 'win32'")],
            [create_dependency("foo", ">=1,<2", marker="sys_platform == 'win32'")],
        ),
        # allow pre-releases
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", allows_prereleases=True)],
            [create_dependency("foo", ">=1", allows_prereleases=True)],
        ),
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", allows_prereleases=False)],
            [create_dependency("foo", ">=1", allows_prereleases=False)],
        ),
        # directory dependency - develop
        (
            [DirectoryDependency("foo", Path("path/to/foo"))],
            [create_dependency("foo", develop=True)],
            [DirectoryDependency("foo", Path("path/to/foo"), develop=True)],
        ),
        # directory dependency - develop (full spec)
        (
            [DirectoryDependency("foo", Path("path/to/foo"))],
            [DirectoryDependency("foo", Path("path/to/foo"), develop=True)],
            [DirectoryDependency("foo", Path("path/to/foo"), develop=True)],
        ),
        # vcs dependency - develop
        (
            [VCSDependency("foo", "git", "https://example.org/foo")],
            [create_dependency("foo", develop=True)],
            [VCSDependency("foo", "git", "https://example.org/foo", develop=True)],
        ),
        # vcs dependency - develop (full spec)
        (
            [VCSDependency("foo", "git", "https://example.org/foo")],
            [VCSDependency("foo", "git", "https://example.org/foo", develop=True)],
            [VCSDependency("foo", "git", "https://example.org/foo", develop=True)],
        ),
        # replace with directory dependency
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [DirectoryDependency("foo", Path("path/to/foo"), develop=True)],
            [DirectoryDependency("foo", Path("path/to/foo"), develop=True)],
        ),
        # source
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", source_name="src")],
            [create_dependency("foo", ">=1", source_name="src")],
        ),
        # different sources depending on marker
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [
                create_dependency(
                    "foo", source_name="src1", marker="sys_platform == 'win32'"
                ),
                create_dependency(
                    "foo", source_name="src2", marker="sys_platform == 'linux'"
                ),
            ],
            [
                create_dependency(
                    "foo", ">=1", source_name="src1", marker="sys_platform == 'win32'"
                ),
                create_dependency(
                    "foo", ">=1", source_name="src2", marker="sys_platform == 'linux'"
                ),
            ],
        ),
        # pairwise different sources depending on marker
        (
            [
                Dependency.create_from_pep_508("foo>=1; sys_platform == 'win32'"),
                Dependency.create_from_pep_508("foo>=1.1; sys_platform == 'linux'"),
            ],
            [
                create_dependency(
                    "foo", source_name="src1", marker="sys_platform == 'win32'"
                ),
                create_dependency(
                    "foo", source_name="src2", marker="sys_platform == 'linux'"
                ),
            ],
            [
                create_dependency(
                    "foo", ">=1", source_name="src1", marker="sys_platform == 'win32'"
                ),
                create_dependency(
                    "foo", ">=1.1", source_name="src2", marker="sys_platform == 'linux'"
                ),
            ],
        ),
        # enrich only one with source
        (
            [
                Dependency.create_from_pep_508("foo>=1; sys_platform == 'win32'"),
                Dependency.create_from_pep_508("foo>=1.1; sys_platform == 'linux'"),
            ],
            [
                create_dependency(
                    "foo", source_name="src1", marker="sys_platform == 'win32'"
                ),
            ],
            [
                create_dependency(
                    "foo", ">=1", source_name="src1", marker="sys_platform == 'win32'"
                ),
                create_dependency("foo", ">=1.1", marker="sys_platform == 'linux'"),
            ],
        ),
        # extras
        (
            [Dependency.create_from_pep_508("foo[extra1,extra2]")],
            [create_dependency("foo", source_name="src")],
            [create_dependency("foo", source_name="src", extras=("extra1", "extra2"))],
        ),
        (
            [Dependency.create_from_pep_508("foo;extra=='extra1'")],
            [create_dependency("foo", source_name="src", optional=True)],
            [create_dependency("foo", source_name="src", marker="extra == 'extra1'")],
        ),
        (
            [Dependency.create_from_pep_508("foo;extra=='extra1'")],
            [create_dependency("foo", source_name="src")],
            (
                [
                    create_dependency(
                        "foo", source_name="src", marker="extra == 'extra1'"
                    )
                ],
                [
                    create_dependency(
                        "foo", source_name="src", marker="extra == 'extra1'"
                    ),
                    create_dependency("foo", source_name="src"),
                ],
            ),
        ),
        # extras - special
        # root extras do not have an extra marker, they just have set _in_extras!
        (
            [
                create_dependency(
                    "foo", source_name="src", optional=True, in_extras=("extra1",)
                )
            ],
            [create_dependency("foo", source_name="src", optional=True)],
            [
                create_dependency(
                    "foo", source_name="src", optional=True, in_extras=("extra1",)
                )
            ],
        ),
        (
            [
                create_dependency(
                    "foo", source_name="src", optional=True, in_extras=("extra1",)
                )
            ],
            [create_dependency("foo", source_name="src")],
            (
                [
                    create_dependency(
                        "foo", source_name="src", optional=True, in_extras=("extra1",)
                    )
                ],
                [
                    create_dependency(
                        "foo", source_name="src", optional=True, in_extras=("extra1",)
                    ),
                    create_dependency("foo", source_name="src"),
                ],
            ),
        ),
        (
            [
                Dependency.create_from_pep_508("foo;extra!='extra1'"),
                create_dependency("foo", in_extras=("extra1",)),
            ],
            [
                create_dependency("foo", marker="extra!='extra1'", source_name="src1"),
                create_dependency("foo", marker="extra=='extra1'", source_name="src2"),
            ],
            [
                create_dependency("foo", source_name="src1", marker="extra!='extra1'"),
                create_dependency("foo", source_name="src2", in_extras=("extra1",)),
            ],
        ),
        (
            [
                Dependency.create_from_pep_508(
                    "foo;extra!='extra1' and extra!='extra2'"
                ),
                create_dependency("foo", in_extras=("extra1", "extra2")),
            ],
            [
                create_dependency(
                    "foo",
                    marker="extra!='extra1' and extra!='extra2'",
                    source_name="src1",
                ),
                create_dependency(
                    "foo",
                    marker="extra=='extra1' or extra=='extra2'",
                    source_name="src2",
                ),
            ],
            [
                create_dependency(
                    "foo",
                    source_name="src1",
                    marker="extra!='extra1' and extra!='extra2'",
                ),
                create_dependency(
                    "foo", source_name="src2", in_extras=("extra1", "extra2")
                ),
            ],
        ),
        (
            [
                create_dependency(
                    "foo", marker="extra!='extra2'", in_extras=("extra1",)
                ),
                create_dependency(
                    "foo", marker="extra!='extra1'", in_extras=("extra2",)
                ),
            ],
            [
                create_dependency(
                    "foo",
                    marker="extra!='extra2' and extra=='extra1'",
                    source_name="src1",
                ),
                create_dependency(
                    "foo",
                    marker="extra!='extra1' and extra=='extra2'",
                    source_name="src2",
                ),
            ],
            [
                create_dependency(
                    "foo",
                    source_name="src1",
                    marker="extra!='extra2'",
                    in_extras=("extra1",),
                ),
                create_dependency(
                    "foo",
                    source_name="src2",
                    marker="extra!='extra1'",
                    in_extras=("extra2",),
                ),
            ],
        ),
    ],
)
def test_dependencies_for_locking(
    dependencies: list[Dependency],
    poetry_dependencies: list[Dependency],
    mixed_dynamic: bool,
    expected_dependencies: list[Dependency] | tuple[list[Dependency], list[Dependency]],
) -> None:
    group = DependencyGroup(name="group", mixed_dynamic=mixed_dynamic)
    group._dependencies = dependencies
    group._poetry_dependencies = poetry_dependencies

    if isinstance(expected_dependencies, tuple):
        expected_dependencies = (
            expected_dependencies[1] if mixed_dynamic else expected_dependencies[0]
        )

    assert group.dependencies_for_locking == expected_dependencies
    # explicitly check attributes that are not considered in __eq__
    assert [d.allows_prereleases() for d in group.dependencies_for_locking] == [
        d.allows_prereleases() for d in expected_dependencies
    ]
    assert [d.source_name for d in group.dependencies_for_locking] == [
        d.source_name for d in expected_dependencies
    ]
    assert [d.marker for d in group.dependencies_for_locking] == [
        d.marker for d in expected_dependencies
    ]
    assert [d._develop for d in group.dependencies_for_locking] == [
        d._develop for d in expected_dependencies
    ]
    assert [d.in_extras for d in group.dependencies_for_locking] == [
        d.in_extras for d in expected_dependencies
    ]
    assert [d.is_optional() for d in group.dependencies_for_locking] == [
        d.is_optional() for d in expected_dependencies
    ]


@pytest.mark.parametrize(
    (
        "dependencies",
        "poetry_dependencies",
    ),
    [
        (
            [Dependency.create_from_pep_508("foo>=1")],
            [create_dependency("foo", "<1")],
        ),
        (
            [DirectoryDependency("foo", Path("path/to/foo"))],
            [VCSDependency("foo", "git", "https://example.org/foo")],
        ),
    ],
)
def test_dependencies_for_locking_failure(
    dependencies: list[Dependency],
    poetry_dependencies: list[Dependency],
) -> None:
    group = DependencyGroup(name="group")
    group._dependencies = dependencies
    group._poetry_dependencies = poetry_dependencies

    with pytest.raises(ValueError):
        _ = group.dependencies_for_locking
