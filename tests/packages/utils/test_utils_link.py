from __future__ import annotations

import uuid

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
    ext: str, file_checksum: str | None = None, metadata_checksum: str | None = None
) -> Link:
    file_checksum = file_checksum or make_checksum()
    return Link(
        "https://files.pythonhosted.org/packages/16/52/dead/"
        f"demo-1.0.0.{ext}#sha256={file_checksum}",
        metadata=f"sha256={metadata_checksum}" if metadata_checksum else None,
    )


def test_package_link_hash(file_checksum: str) -> None:
    link = make_url(ext="whl", file_checksum=file_checksum)
    assert link.hash_name == "sha256"
    assert link.hash == file_checksum
    assert link.show_url == "demo-1.0.0.whl"

    # this is legacy PEP 503, no metadata hash is present
    assert not link.has_metadata
    assert not link.metadata_url
    assert not link.metadata_hash
    assert not link.metadata_hash_name


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
        assert link.metadata_hash == metadata_checksum
        assert link.metadata_hash_name == "sha256"
    else:
        assert not link.has_metadata
        assert not link.metadata_url
        assert not link.metadata_hash
        assert not link.metadata_hash_name


def test_package_link_pep658_no_default_metadata() -> None:
    link = make_url(ext="whl")

    assert not link.has_metadata
    assert not link.metadata_url
    assert not link.metadata_hash
    assert not link.metadata_hash_name


@pytest.mark.parametrize(
    ("metadata", "has_metadata"),
    [
        ("true", True),
        ("false", False),
        ("", False),
    ],
)
def test_package_link_pep653_non_hash_metadata_value(
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

    assert not link.metadata_hash
    assert not link.metadata_hash_name
