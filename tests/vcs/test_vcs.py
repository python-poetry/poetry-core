from __future__ import annotations

import os
import subprocess

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import pytest

from poetry.core.utils._compat import WINDOWS
from poetry.core.vcs import get_vcs
from poetry.core.vcs.git import Git
from poetry.core.vcs.git import GitUrl
from poetry.core.vcs.git import ParsedUrl
from poetry.core.vcs.git import _reset_executable
from poetry.core.vcs.git import executable


if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_mock import MockerFixture


@pytest.fixture
def reset_git() -> Iterator[None]:
    _reset_executable()
    try:
        yield
    finally:
        _reset_executable()


@pytest.fixture(autouse=True)
def with_mocked_get_vcs() -> None:
    # disabled global mocking of get_vcs
    pass


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
            ParsedUrl("ssh", "github.com", ":org/repo", "git", None, "repo", None),
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
            "git+https://username:@github.com/sdispater/pendulum",
            ParsedUrl(
                "https",
                "github.com",
                "/sdispater/pendulum",
                "username:",
                None,
                "pendulum",
                None,
            ),
        ),
        (
            "git+https://username:password@github.com/sdispater/pendulum",
            ParsedUrl(
                "https",
                "github.com",
                "/sdispater/pendulum",
                "username:password",
                None,
                "pendulum",
                None,
            ),
        ),
        (
            "git+https://username+suffix:password@github.com/sdispater/pendulum",
            ParsedUrl(
                "https",
                "github.com",
                "/sdispater/pendulum",
                "username+suffix:password",
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
            "git+ssh://git@git.example.com:sdispater/project/+git/my_repo.git",
            ParsedUrl(
                "ssh",
                "git.example.com",
                ":sdispater/project/+git/my_repo.git",
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


@pytest.mark.skipif(
    not WINDOWS,
    reason=(
        "Retrieving the complete path to git is only necessary on Windows, for security"
        " reasons"
    ),
)
def test_ensure_absolute_path_to_git(reset_git: None, mocker: MockerFixture) -> None:
    def checkout_output(cmd: list[str], *args: Any, **kwargs: Any) -> str | bytes:
        if Path(cmd[0]).name == "where.exe":
            return "\n".join(
                [str(Path.cwd().joinpath("git.exe")), r"C:\Git\cmd\git.exe"]
            )

        return b""

    mock = mocker.patch.object(subprocess, "check_output", side_effect=checkout_output)

    Git().run("config")

    assert mock.call_args_list[-1][0][0] == [r"C:\Git\cmd\git.exe", "config"]

    mock = mocker.patch.object(subprocess, "check_output", return_value=b"")

    Git().run("config")

    assert mock.call_args_list[-1][0][0] == [r"C:\Git\cmd\git.exe", "config"]


def test_get_vcs_encoding(tmp_path: Path) -> None:
    repo_path = tmp_path / "répö"
    repo_path.mkdir()
    assert repo_path.exists()
    assert subprocess.check_call([executable(), "init"], cwd=repo_path) == 0
    vcs = get_vcs(repo_path)
    assert vcs is not None
    assert vcs._work_dir is not None
    assert vcs._work_dir.exists()
    assert vcs._work_dir == repo_path


def test_get_vc_subdir(tmp_path: Path) -> None:
    repo_path = tmp_path / "répö"
    repo_path.mkdir()
    assert repo_path.exists()
    assert subprocess.check_call([executable(), "init"], cwd=repo_path) == 0
    subdir = repo_path / "subdir"
    subdir.mkdir()
    vcs = get_vcs(subdir)
    assert vcs is not None
    assert vcs._work_dir is not None
    assert vcs._work_dir.exists()
    assert vcs._work_dir == repo_path


def test_get_vcs_no_repo(tmp_path: Path, mocker: MockerFixture) -> None:
    repo_path = tmp_path / "répö"
    repo_path.mkdir()
    assert repo_path.exists()
    assert subprocess.check_call([executable(), "init"], cwd=repo_path) == 0

    # This makes sure git fails to find the git directory even if one
    # exists at some higher level in the filesystem
    mocker.patch.dict(os.environ, {"GIT_DIR": os.devnull})

    vcs = get_vcs(repo_path)
    assert vcs is None


def test_get_vcs_ignored_subdir(tmp_path: Path) -> None:
    # See https://github.com/python-poetry/poetry-core/pull/611
    repo_path = tmp_path / "répö"
    repo_path.mkdir()
    assert repo_path.exists()
    assert subprocess.check_call([executable(), "init"], cwd=repo_path) == 0
    (repo_path / ".gitignore").write_text("/ignored", encoding="utf-8")
    subdir = repo_path / "ignored"
    subdir.mkdir()

    vcs = get_vcs(subdir)
    assert vcs is None
