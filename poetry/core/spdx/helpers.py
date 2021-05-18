import json
import os

from typing import TYPE_CHECKING
from typing import Dict
from typing import Optional


if TYPE_CHECKING:
    from .license import License  # noqa


_licenses: Optional[Dict[str, "License"]] = None


def license_by_id(identifier: str) -> "License":
    from .license import License  # noqa

    if _licenses is None:
        load_licenses()

    id = identifier.lower()

    if id not in _licenses:
        if not identifier:
            raise ValueError("A license identifier is required")

        return License(identifier, identifier, False, False)

    return _licenses[id]


def load_licenses() -> None:
    from .license import License  # noqa

    global _licenses

    _licenses = {}

    licenses_file = os.path.join(os.path.dirname(__file__), "data", "licenses.json")

    with open(licenses_file, encoding="utf-8") as f:
        data = json.loads(f.read())

    for name, license_info in data.items():
        license = License(name, license_info[0], license_info[1], license_info[2])
        _licenses[name.lower()] = license

        full_name = license_info[0].lower()
        if full_name in _licenses:
            existing_license = _licenses[full_name]
            if not existing_license.is_deprecated:
                continue

        _licenses[full_name] = license

    # Add a Proprietary license for non-standard licenses
    _licenses["proprietary"] = License("Proprietary", "Proprietary", False, False)


if __name__ == "__main__":
    from .updater import Updater

    updater = Updater()
    updater.dump()
