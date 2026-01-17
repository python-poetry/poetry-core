from __future__ import annotations

import uuid

from datetime import datetime
from datetime import timezone
from hashlib import sha256

import pytest

from poetry.core.packages.utils.link import Link


def make_checksum() -> str:
    return sha256(str(uuid.uuid4()).encode()).hexdigest()


@pytest.fixture()
def file_checksum() -> str:
    return make_checksum()


@pytest.fixture()
def metadata_checksum() -> str:
    return make_checksum()


def make_url(
    ext: str,
    *,
    file_checksum: str | None = None,
    metadata_checksum: str | None = None,
    hashes: dict[str, str] | None = None,
    metadata: dict[str, str] | str | None = None,
) -> Link:
    url = f"https://files.pythonhosted.org/packages/16/52/dead/demo-1.0.0.{ext}"
    if not hashes:
        file_checksum = file_checksum or make_checksum()
        url += f"#sha256={file_checksum}"
    if not metadata:
        metadata = f"sha256={metadata_checksum}" if metadata_checksum else None
    return Link(url, hashes=hashes, metadata=metadata)


def test_package_link_hash(file_checksum: str) -> None:
    link = make_url(ext="whl", file_checksum=file_checksum)
    assert link.hashes == {"sha256": file_checksum}
    assert link.show_url == "demo-1.0.0.whl"

    # this is legacy PEP 503, no metadata hash is present
    assert not link.has_metadata
    assert not link.metadata_url
    assert not link.metadata_hashes


def test_package_link_hashes(file_checksum: str) -> None:
    link = make_url(ext="whl", hashes={"sha256": file_checksum, "other": "1234"})
    assert link.hashes == {"sha256": file_checksum, "other": "1234"}
    assert link.show_url == "demo-1.0.0.whl"


@pytest.mark.parametrize(
    ("ext", "check"),
    [
        ("whl", "wheel"),
        ("egg", "egg"),
        ("tar.gz", "sdist"),
        ("zip", "sdist"),
        ("cp36-cp36m-manylinux1_x86_64.whl", "wheel"),
    ],
)
def test_package_link_is_checks(ext: str, check: str) -> None:
    link = make_url(ext=ext)
    assert getattr(link, f"is_{check}")


@pytest.mark.parametrize(
    ("ext", "has_metadata"),
    [("whl", True), ("egg", False), ("tar.gz", True), ("zip", True)],
)
def test_package_link_pep658(
    ext: str, has_metadata: bool, metadata_checksum: str
) -> None:
    link = make_url(ext=ext, metadata_checksum=metadata_checksum)

    if has_metadata:
        assert link.has_metadata
        assert link.metadata_url == f"{link.url_without_fragment}.metadata"
        assert link.metadata_hashes == {"sha256": metadata_checksum}
    else:
        assert not link.has_metadata
        assert not link.metadata_url
        assert not link.metadata_hashes


def test_package_link_pep658_no_default_metadata() -> None:
    link = make_url(ext="whl")

    assert not link.has_metadata
    assert not link.metadata_url
    assert not link.metadata_hashes


@pytest.mark.parametrize(
    ("metadata", "has_metadata"),
    [
        ("true", True),
        ("false", False),
        ("", False),
    ],
)
def test_package_link_pep658_non_hash_metadata_value(
    file_checksum: str, metadata: str | bool, has_metadata: bool
) -> None:
    link = Link(
        "https://files.pythonhosted.org/packages/16/52/dead/"
        f"demo-1.0.0.whl#sha256={file_checksum}",
        metadata=metadata,
    )

    if has_metadata:
        assert link.has_metadata
        assert link.metadata_url == f"{link.url_without_fragment}.metadata"
    else:
        assert not link.has_metadata
        assert not link.metadata_url

    assert not link.metadata_hashes


def test_package_link_pep691() -> None:
    link = make_url(ext="whl", metadata={"sha256": "abcd", "sha512": "1234"})

    assert link.has_metadata
    assert link.metadata_url == f"{link.url_without_fragment}.metadata"
    assert link.metadata_hashes == {"sha256": "abcd", "sha512": "1234"}


def test_package_link_pep592_default_not_yanked() -> None:
    link = make_url(ext="whl")

    assert not link.yanked
    assert link.yanked_reason == ""


@pytest.mark.parametrize(
    ("yanked", "expected_yanked", "expected_yanked_reason"),
    [
        (True, True, ""),
        (False, False, ""),
        ("the reason", True, "the reason"),
        ("", True, ""),
    ],
)
def test_package_link_pep592_yanked(
    yanked: str | bool, expected_yanked: bool, expected_yanked_reason: str
) -> None:
    link = Link("https://example.org", yanked=yanked)

    assert link.yanked == expected_yanked
    assert link.yanked_reason == expected_yanked_reason


def test_package_link_size_default_is_none() -> None:
    link = Link("https://example.org")

    assert link.size is None


def test_package_link_size() -> None:
    link = Link("https://example.org", size=1234)

    assert link.size == 1234


def test_package_link_upload_time_default_is_none() -> None:
    link = Link("https://example.org")

    assert link.upload_time is None


@pytest.mark.parametrize(
    ("upload_time", "expected"),
    [
        ("2023-06-15T08:30:45Z", datetime(2023, 6, 15, 8, 30, 45, tzinfo=timezone.utc)),
        (
            "2022-12-31T23:59:59+00:00",
            datetime(2022, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        ),
        (
            "2023-06-15T08:30:45.123456Z",
            datetime(2023, 6, 15, 8, 30, 45, 123456, tzinfo=timezone.utc),
        ),
        (
            "2023-06-15T10:30:45+02:00",
            datetime(2023, 6, 15, 8, 30, 45, tzinfo=timezone.utc),
        ),
        ("not-a-timestamp", None),
    ],
)
def test_package_link_upload_time(upload_time: str, expected: datetime) -> None:
    link = Link("https://example.org", upload_time=upload_time)

    assert link.upload_time == expected
