from __future__ import annotations

import subprocess

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import pytest

from poetry.core.utils._compat import WINDOWS
from poetry.core.vcs.git import Git
from poetry.core.vcs.git import GitError
from poetry.core.vcs.git import GitUrl
from poetry.core.vcs.git import ParsedUrl
from poetry.core.vcs.git import _reset_executable


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    "url, normalized",
    [
        (
            "git+ssh://user@hostname:project.git#commit",
            GitUrl("user@hostname:project.git", "commit", None),
        ),
        (
            "git+http://user@hostname/project/blah.git@commit",
            GitUrl("http://user@hostname/project/blah.git", "commit", None),
        ),
        (
            "git+https://user@hostname/project/blah.git",
            GitUrl("https://user@hostname/project/blah.git", None, None),
        ),
        (
            "git+https://user@hostname/project%20~_-.foo/blah%20~_-.bar.git",
            GitUrl(
                "https://user@hostname/project%20~_-.foo/blah%20~_-.bar.git", None, None
            ),
        ),
        (
            "git+https://user@hostname:project/blah.git",
            GitUrl("https://user@hostname/project/blah.git", None, None),
        ),
        (
            "git+ssh://git@github.com:sdispater/poetry.git#v1.0.27",
            GitUrl("git@github.com:sdispater/poetry.git", "v1.0.27", None),
        ),
        (
            "git+ssh://git@github.com:/sdispater/poetry.git",
            GitUrl("git@github.com:/sdispater/poetry.git", None, None),
        ),
        (
            "git+ssh://git@github.com:org/repo",
            GitUrl("git@github.com:org/repo", None, None),
        ),
        (
            "git+ssh://git@github.com/org/repo",
            GitUrl("ssh://git@github.com/org/repo", None, None),
        ),
        ("git+ssh://foo:22/some/path", GitUrl("ssh://foo:22/some/path", None, None)),
        ("git@github.com:org/repo", GitUrl("git@github.com:org/repo", None, None)),
        (
            "git+https://github.com/sdispater/pendulum",
            GitUrl("https://github.com/sdispater/pendulum", None, None),
        ),
        (
            "git+https://github.com/sdispater/pendulum#7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            GitUrl(
                "https://github.com/sdispater/pendulum",
                "7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
                None,
            ),
        ),
        (
            "git+ssh://git@git.example.com:b/b.git#v1.0.0",
            GitUrl("git@git.example.com:b/b.git", "v1.0.0", None),
        ),
        (
            "git+ssh://git@github.com:sdispater/pendulum.git#foo/bar",
            GitUrl("git@github.com:sdispater/pendulum.git", "foo/bar", None),
        ),
        ("git+file:///foo/bar.git", GitUrl("file:///foo/bar.git", None, None)),
        (
            "git+file://C:\\Users\\hello\\testing.git#zkat/windows-files",
            GitUrl("file://C:\\Users\\hello\\testing.git", "zkat/windows-files", None),
        ),
        # hidden directories on Windows use $ in their path
        # python-poetry/poetry#5493
        (
            "git+file://C:\\Users\\hello$\\testing.git#zkat/windows-files",
            GitUrl("file://C:\\Users\\hello$\\testing.git", "zkat/windows-files", None),
        ),
        (
            "git+https://git.example.com/sdispater/project/my_repo.git",
            GitUrl("https://git.example.com/sdispater/project/my_repo.git", None, None),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git",
            GitUrl("git@git.example.com:sdispater/project/my_repo.git", None, None),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git#subdirectory=project",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                None,
                "project",
            ),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git@commit#subdirectory=project",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                "commit",
                "project",
            ),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git#commit&subdirectory=project",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                "commit",
                "project",
            ),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git#commit#subdirectory=project",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                "commit",
                "project",
            ),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git@commit&subdirectory=project",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                "commit",
                "project",
            ),
        ),
        (
            "git+https://github.com/demo/pyproject-demo-subdirectory.git@subdirectory#subdirectory=subdirectory",
            GitUrl(
                "https://github.com/demo/pyproject-demo-subdirectory.git",
                "subdirectory",
                "subdirectory",
            ),
        ),
    ],
)
def test_normalize_url(url: str, normalized: GitUrl) -> None:
    assert Git.normalize_url(url) == normalized


@pytest.mark.parametrize(
    "url, parsed",
    [
        (
            "git+ssh://user@hostname:project.git#commit",
            ParsedUrl(
                "ssh", "hostname", ":project.git", "user", None, "project", "commit"
            ),
        ),
        (
            "git+http://user@hostname/project/blah.git@commit",
            ParsedUrl(
                "http", "hostname", "/project/blah.git", "user", None, "blah", "commit"
            ),
        ),
        (
            "git+https://user@hostname/project/blah.git",
            ParsedUrl(
                "https", "hostname", "/project/blah.git", "user", None, "blah", None
            ),
        ),
        (
            "git+https://user@hostname/project%20~_-.foo/blah%20~_-.bar.git",
            ParsedUrl(
                "https",
                "hostname",
                "/project%20~_-.foo/blah%20~_-.bar.git",
                "user",
                None,
                "blah%20~_-.bar",
                None,
            ),
        ),
        (
            "git+https://user@hostname:project/blah.git",
            ParsedUrl(
                "https", "hostname", ":project/blah.git", "user", None, "blah", None
            ),
        ),
        (
            "git+ssh://git@github.com:sdispater/poetry.git#v1.0.27",
            ParsedUrl(
                "ssh",
                "github.com",
                ":sdispater/poetry.git",
                "git",
                None,
                "poetry",
                "v1.0.27",
            ),
        ),
        (
            "git+ssh://git@github.com:sdispater/poetry.git#egg=name",
            ParsedUrl(
                "ssh",
                "github.com",
                ":sdispater/poetry.git",
                "git",
                None,
                "poetry",
                None,
            ),
        ),
        (
            "git+ssh://git@github.com:/sdispater/poetry.git",
            ParsedUrl(
                "ssh",
                "github.com",
                ":/sdispater/poetry.git",
                "git",
                None,
                "poetry",
                None,
            ),
        ),
        (
            "git+ssh://git@github.com:org/repo",
            ParsedUrl("ssh", "github.com", ":org/repo", "git", None, "repo", None),
        ),
        (
            "git+ssh://git@github.com/org/repo",
            ParsedUrl("ssh", "github.com", "/org/repo", "git", None, "repo", None),
        ),
        (
            "git+ssh://foo:22/some/path",
            ParsedUrl("ssh", "foo", "/some/path", None, "22", "path", None),
        ),
        (
            "git@github.com:org/repo",
            ParsedUrl(None, "github.com", ":org/repo", "git", None, "repo", None),
        ),
        (
            "git+https://github.com/sdispater/pendulum",
            ParsedUrl(
                "https",
                "github.com",
                "/sdispater/pendulum",
                None,
                None,
                "pendulum",
                None,
            ),
        ),
        (
            "git+https://github.com/sdispater/pendulum#7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            ParsedUrl(
                "https",
                "github.com",
                "/sdispater/pendulum",
                None,
                None,
                "pendulum",
                "7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            ),
        ),
        (
            "git+ssh://git@git.example.com:b/b.git#v1.0.0",
            ParsedUrl("ssh", "git.example.com", ":b/b.git", "git", None, "b", "v1.0.0"),
        ),
        (
            "git+ssh://git@github.com:sdispater/pendulum.git#foo/bar",
            ParsedUrl(
                "ssh",
                "github.com",
                ":sdispater/pendulum.git",
                "git",
                None,
                "pendulum",
                "foo/bar",
            ),
        ),
        (
            "git+file:///foo/bar.git",
            ParsedUrl("file", None, "/foo/bar.git", None, None, "bar", None),
        ),
        (
            "git+file://C:\\Users\\hello\\testing.git#zkat/windows-files",
            ParsedUrl(
                "file",
                "C",
                ":\\Users\\hello\\testing.git",
                None,
                None,
                "testing",
                "zkat/windows-files",
            ),
        ),
        (
            "git+https://git.example.com/sdispater/project/my_repo.git",
            ParsedUrl(
                "https",
                "git.example.com",
                "/sdispater/project/my_repo.git",
                None,
                None,
                "my_repo",
                None,
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                None,
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git#subdirectory=project-dir",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                None,
                "project-dir",
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git#commit&subdirectory=project-dir",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                "commit",
                "project-dir",
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git@commit#subdirectory=project-dir",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                "commit",
                "project-dir",
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git@commit&subdirectory=project_dir",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                "commit",
                "project_dir",
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git@commit#egg=package&subdirectory=project_dir",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/my_repo.git",
                "git",
                None,
                "my_repo",
                "commit",
                "project_dir",
            ),
        ),
    ],
)
def test_parse_url(url: str, parsed: ParsedUrl) -> None:
    result = ParsedUrl.parse(url)
    assert result.name == parsed.name
    assert result.pathname == parsed.pathname
    assert result.port == parsed.port
    assert result.protocol == parsed.protocol
    assert result.resource == parsed.resource
    assert result.rev == parsed.rev
    assert result.url == parsed.url
    assert result.user == parsed.user
    assert result.subdirectory == parsed.subdirectory


def test_parse_url_should_fail() -> None:
    url = "https://" + "@" * 64 + "!"

    with pytest.raises(ValueError):
        ParsedUrl.parse(url)


def test_git_clone_raises_error_on_invalid_repository() -> None:
    with pytest.raises(GitError):
        Git().clone("-u./payload", Path("foo"))


def test_git_checkout_raises_error_on_invalid_repository() -> None:
    with pytest.raises(GitError):
        Git().checkout("-u./payload")


def test_git_rev_parse_raises_error_on_invalid_repository() -> None:
    with pytest.raises(GitError):
        Git().rev_parse("-u./payload")


@pytest.mark.skipif(
    not WINDOWS,
    reason=(
        "Retrieving the complete path to git is only necessary on Windows, for security"
        " reasons"
    ),
)
def test_ensure_absolute_path_to_git(mocker: MockerFixture) -> None:
    _reset_executable()

    def checkout_output(cmd: list[str], *args: Any, **kwargs: Any) -> str | bytes:
        if Path(cmd[0]).name == "where.exe":
            return "\n".join(
                [
                    str(Path.cwd().joinpath("git.exe")),
                    "C:\\Git\\cmd\\git.exe",
                ]
            )

        return b""

    mock = mocker.patch.object(subprocess, "check_output", side_effect=checkout_output)

    Git().run("config")

    assert mock.call_args_list[-1][0][0] == [
        "C:\\Git\\cmd\\git.exe",
        "config",
    ]


@pytest.mark.skipif(
    not WINDOWS,
    reason=(
        "Retrieving the complete path to git is only necessary on Windows, for security"
        " reasons"
    ),
)
def test_ensure_existing_git_executable_is_found(mocker: MockerFixture) -> None:
    mock = mocker.patch.object(subprocess, "check_output", return_value=b"")

    Git().run("config")

    cmd = Path(mock.call_args_list[-1][0][0][0])

    assert cmd.is_absolute()
    assert cmd.name == "git.exe"
