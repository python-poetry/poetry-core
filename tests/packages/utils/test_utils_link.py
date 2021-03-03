import uuid

from hashlib import sha256

from poetry.core.packages.utils.link import Link


def make_url(ext):
    checksum = sha256(str(uuid.uuid4()).encode())
    return Link(
        "https://files.pythonhosted.org/packages/16/52/dead/"
        "demo-1.0.0.{}#sha256={}".format(ext, checksum)
    )


def test_package_link_is_checks():
    assert make_url("egg").is_egg
    assert make_url("tar.gz").is_sdist
    assert make_url("zip").is_sdist
    assert make_url("exe").is_wininst
    assert make_url("cp36-cp36m-manylinux1_x86_64.whl").is_wheel
