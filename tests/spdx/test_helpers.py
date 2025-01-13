from __future__ import annotations

import pytest

from poetry.core.spdx.helpers import _load_licenses
from poetry.core.spdx.helpers import license_by_id


def test_license_by_id() -> None:
    license = license_by_id("MIT")

    assert license.id == "MIT"
    assert license.name == "MIT License"
    assert license.is_osi_approved
    assert not license.is_deprecated

    license = license_by_id("LGPL-3.0-or-later")

    assert license.id == "LGPL-3.0-or-later"
    assert license.name == "GNU Lesser General Public License v3.0 or later"
    assert license.is_osi_approved
    assert not license.is_deprecated


def test_license_by_id_is_case_insensitive() -> None:
    license = license_by_id("mit")

    assert license.id == "MIT"

    license = license_by_id("miT")

    assert license.id == "MIT"


def test_license_by_id_with_full_name() -> None:
    license = license_by_id("GNU Lesser General Public License v3.0 or later")

    assert license.id == "LGPL-3.0-or-later"
    assert license.name == "GNU Lesser General Public License v3.0 or later"
    assert license.is_osi_approved
    assert not license.is_deprecated


def test_license_by_id_invalid() -> None:
    with pytest.raises(ValueError):
        license_by_id("")


def test_license_by_id_custom() -> None:
    license = license_by_id("Custom")

    assert license.id == "Custom"
    assert license.name == "Custom"
    assert not license.is_osi_approved
    assert not license.is_deprecated


def test_valid_trove_classifiers() -> None:
    import trove_classifiers

    licenses = _load_licenses()

    for license_id, license in licenses.items():
        classifier = license.classifier
        valid_classifier = classifier in trove_classifiers.classifiers

        assert valid_classifier, (
            f"'{license_id}' returns invalid classifier '{classifier}'"
        )
