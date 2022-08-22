from __future__ import annotations

from poetry.core.spdx.helpers import license_by_id


def test_classifier_name() -> None:
    license = license_by_id("lgpl-3.0-or-later")

    assert (
        license.classifier_name
        == "GNU Lesser General Public License v3 or later (LGPLv3+)"
    )


def test_classifier_name_no_classifer_osi_approved() -> None:
    license = license_by_id("LiLiQ-R-1.1")

    assert license.classifier_name is None


def test_classifier_name_no_classifer() -> None:
    license = license_by_id("Leptonica")

    assert license.classifier_name == "Other/Proprietary License"


def test_classifier() -> None:
    license = license_by_id("lgpl-3.0-or-later")

    assert (
        license.classifier
        == "License :: "
        "OSI Approved :: "
        "GNU Lesser General Public License v3 or later (LGPLv3+)"
    )


def test_classifier_no_classifer_osi_approved() -> None:
    license = license_by_id("LiLiQ-R-1.1")

    assert license.classifier == "License :: OSI Approved"


def test_classifier_no_classifer() -> None:
    license = license_by_id("Leptonica")

    assert license.classifier == "License :: Other/Proprietary License"


def test_proprietary_license() -> None:
    license = license_by_id("Proprietary")

    assert license.classifier == "License :: Other/Proprietary License"


def test_custom_license() -> None:
    license = license_by_id("Amazon Software License")

    assert license.classifier == "License :: Other/Proprietary License"
