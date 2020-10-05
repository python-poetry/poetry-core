import pytest

from poetry.core.vcs.git import Git
from poetry.core.vcs.git import GitUrl
from poetry.core.vcs.git import ParsedUrl


@pytest.mark.parametrize(
    "url, normalized",
    [
        (
            "git+ssh://user@hostname:project.git#commit",
            GitUrl("user@hostname:project.git", "commit"),
        ),
        (
            "git+http://user@hostname/project/blah.git@commit",
            GitUrl("http://user@hostname/project/blah.git", "commit"),
        ),
        (
            "git+https://user@hostname/project/blah.git",
            GitUrl("https://user@hostname/project/blah.git", None),
        ),
        (
            "git+https://user@hostname/project~_-.foo/blah~_-.bar.git",
            GitUrl("https://user@hostname/project~_-.foo/blah~_-.bar.git", None),
        ),
        (
            "git+https://user@hostname:project/blah.git",
            GitUrl("https://user@hostname/project/blah.git", None),
        ),
        (
            "git+ssh://git@github.com:sdispater/poetry.git#v1.0.27",
            GitUrl("git@github.com:sdispater/poetry.git", "v1.0.27"),
        ),
        (
            "git+ssh://git@github.com:/sdispater/poetry.git",
            GitUrl("git@github.com:/sdispater/poetry.git", None),
        ),
        ("git+ssh://git@github.com:org/repo", GitUrl("git@github.com:org/repo", None),),
        (
            "git+ssh://git@github.com/org/repo",
            GitUrl("ssh://git@github.com/org/repo", None),
        ),
        ("git+ssh://foo:22/some/path", GitUrl("ssh://foo:22/some/path", None)),
        ("git@github.com:org/repo", GitUrl("git@github.com:org/repo", None)),
        (
            "git+https://github.com/sdispater/pendulum",
            GitUrl("https://github.com/sdispater/pendulum", None),
        ),
        (
            "git+https://github.com/sdispater/pendulum#7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            GitUrl(
                "https://github.com/sdispater/pendulum",
                "7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            ),
        ),
        (
            "git+ssh://git@git.example.com:b/b.git#v1.0.0",
            GitUrl("git@git.example.com:b/b.git", "v1.0.0"),
        ),
        (
            "git+ssh://git@github.com:sdispater/pendulum.git#foo/bar",
            GitUrl("git@github.com:sdispater/pendulum.git", "foo/bar"),
        ),
        ("git+file:///foo/bar.git", GitUrl("file:///foo/bar.git", None)),
        (
            "git+file://C:\\Users\\hello\\testing.git#zkat/windows-files",
            GitUrl("file://C:\\Users\\hello\\testing.git", "zkat/windows-files"),
        ),
        (
            "git+https://git.example.com/sdispater/project/my_repo.git",
            GitUrl("https://git.example.com/sdispater/project/my_repo.git", None),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git",
            GitUrl("git@git.example.com:sdispater/project/my_repo.git", None),
        ),
        (
            "git+https://user:fafb334-cb038533f851c23d0b63254223Abf72ce4f02987e7064b0c95566699a@hostname/project/blah.git",
            GitUrl(
                "https://user:fafb334-cb038533f851c23d0b63254223Abf72ce4f02987e7064b0c95566699a@hostname/project/blah.git",
                None,
            ),
        ),
    ],
)
def test_normalize_url(url, normalized):
    assert normalized == Git.normalize_url(url)


@pytest.mark.parametrize(
    "url, parsed",
    [
        (
            "git+ssh://user@hostname:project.git#commit",
            ParsedUrl(
                protocol="ssh",
                resource="hostname",
                pathname=":project.git",
                user="user",
                name="project",
                rev="commit",
            ),
        ),
        (
            "git+http://user@hostname/project/blah.git@commit",
            ParsedUrl(
                protocol="http",
                resource="hostname",
                pathname="/project/blah.git",
                user="user",
                name="blah",
                rev="commit",
            ),
        ),
        (
            "git+https://user@hostname/project/blah.git",
            ParsedUrl(
                protocol="https",
                resource="hostname",
                pathname="/project/blah.git",
                user="user",
                name="blah",
            ),
        ),
        (
            "git+https://user@hostname/project~_-.foo/blah~_-.bar.git",
            ParsedUrl(
                protocol="https",
                resource="hostname",
                pathname="/project~_-.foo/blah~_-.bar.git",
                user="user",
                name="blah~_-.bar",
            ),
        ),
        (
            "git+https://user@hostname:project/blah.git",
            ParsedUrl(
                protocol="https",
                resource="hostname",
                pathname=":project/blah.git",
                user="user",
                name="blah",
            ),
        ),
        (
            "git+ssh://git@github.com:sdispater/poetry.git#v1.0.27",
            ParsedUrl(
                protocol="ssh",
                resource="github.com",
                pathname=":sdispater/poetry.git",
                user="git",
                name="poetry",
                rev="v1.0.27",
            ),
        ),
        (
            "git+ssh://git@github.com:/sdispater/poetry.git",
            ParsedUrl(
                protocol="ssh",
                resource="github.com",
                pathname=":/sdispater/poetry.git",
                user="git",
                name="poetry",
            ),
        ),
        (
            "git+ssh://git@github.com:org/repo",
            ParsedUrl(
                protocol="ssh",
                resource="github.com",
                pathname=":org/repo",
                user="git",
                name="repo",
            ),
        ),
        (
            "git+ssh://git@github.com/org/repo",
            ParsedUrl(
                protocol="ssh",
                resource="github.com",
                pathname="/org/repo",
                user="git",
                name="repo",
            ),
        ),
        (
            "git+ssh://foo:22/some/path",
            ParsedUrl(
                protocol="ssh",
                resource="foo",
                pathname="/some/path",
                port="22",
                name="path",
            ),
        ),
        (
            "git@github.com:org/repo",
            ParsedUrl(
                resource="github.com", pathname=":org/repo", user="git", name="repo",
            ),
        ),
        (
            "git+https://github.com/sdispater/pendulum",
            ParsedUrl(
                protocol="https",
                resource="github.com",
                pathname="/sdispater/pendulum",
                name="pendulum",
            ),
        ),
        (
            "git+https://github.com/sdispater/pendulum#7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            ParsedUrl(
                protocol="https",
                resource="github.com",
                pathname="/sdispater/pendulum",
                name="pendulum",
                rev="7a018f2d075b03a73409e8356f9b29c9ad4ea2c5",
            ),
        ),
        (
            "git+ssh://git@git.example.com:b/b.git#v1.0.0",
            ParsedUrl(
                protocol="ssh",
                resource="git.example.com",
                pathname=":b/b.git",
                user="git",
                name="b",
                rev="v1.0.0",
            ),
        ),
        (
            "git+ssh://git@github.com:sdispater/pendulum.git#foo/bar",
            ParsedUrl(
                protocol="ssh",
                resource="github.com",
                pathname=":sdispater/pendulum.git",
                user="git",
                name="pendulum",
                rev="foo/bar",
            ),
        ),
        (
            "git+file:///foo/bar.git",
            ParsedUrl(protocol="file", pathname="/foo/bar.git", name="bar",),
        ),
        (
            "git+file://C:\\Users\\hello\\testing.git#zkat/windows-files",
            ParsedUrl(
                protocol="file",
                resource="C",
                pathname=":\\Users\\hello\\testing.git",
                name="testing",
                rev="zkat/windows-files",
            ),
        ),
        (
            "git+https://git.example.com/sdispater/project/my_repo.git",
            ParsedUrl(
                protocol="https",
                resource="git.example.com",
                pathname="/sdispater/project/my_repo.git",
                name="my_repo",
            ),
        ),
        (
            "git+ssh://git@git.example.com:sdispater/project/my_repo.git",
            ParsedUrl(
                protocol="ssh",
                resource="git.example.com",
                pathname=":sdispater/project/my_repo.git",
                user="git",
                name="my_repo",
            ),
        ),
        (
            "git+https://user:fafb334-cb038533f851c23d0b63254223Abf72ce4f02987e7064b0c95566699a@hostname/project/blah.git",
            ParsedUrl(
                protocol="https",
                resource="hostname",
                pathname="/project/blah.git",
                user="user",
                password="fafb334-cb038533f851c23d0b63254223Abf72ce4f02987e7064b0c95566699a",
                name="blah",
            ),
        ),
    ],
)
def test_parse_url(url, parsed):
    result = ParsedUrl.parse(url)
    assert parsed.name == result.name
    assert parsed.pathname == result.pathname
    assert parsed.port == result.port
    assert parsed.protocol == result.protocol
    assert parsed.resource == result.resource
    assert parsed.rev == result.rev
    assert parsed.url == result.url
    assert parsed.user == result.user
    assert parsed.password == result.password


def test_parse_url_should_fail():
    url = "https://" + "@" * 64 + "!"

    with pytest.raises(ValueError):
        ParsedUrl.parse(url)


@pytest.mark.parametrize(
    ["url", "is_unsafe"],
    [
        (
            ParsedUrl(
                protocol="ssh",
                resource="git.example.com",
                pathname=":sdispater/project/my_repo.git",
                user="git",
                name="my_repo",
            ),
            False,
        ),
        (
            ParsedUrl(
                protocol="https",
                resource="hostname",
                pathname="/project/blah.git",
                user="user",
                password="fafb334-cb038533f851c23d0b63254223Abf72ce4f02987e7064b0c95566699a",
                name="blah",
            ),
            True,
        ),
    ],
)
def test_is_unsafe(url, is_unsafe):
    assert url.is_unsafe == is_unsafe
