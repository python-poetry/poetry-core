import json
import os

from io import open
from typing import Dict
from typing import Optional

from .license import License


_licenses: Optional[Dict[str, License]] = None


def license_by_id(identifier: str) -> License:

    licenses = _lazy_load_licenses()

    id = identifier.lower()

    if id not in licenses:
        if not identifier:
            raise ValueError("A license identifier is required")

        return License(identifier, identifier, False, False)

    return licenses[id]


def _lazy_load_licenses() -> Dict[str, License]:

    global _licenses

    if _licenses is None:
        licenses = _load_licenses()
        _licenses = licenses
        return licenses
    else:
        return _licenses


def _load_licenses() -> Dict[str, License]:

    licenses = {}
    licenses_file = os.path.join(os.path.dirname(__file__), "data", "licenses.json")

    with open(licenses_file, encoding="utf-8") as f:
        data = json.loads(f.read())

    for name, license_info in data.items():
        license = License(name, license_info[0], license_info[1], license_info[2])
        licenses[name.lower()] = license

        full_name = license_info[0].lower()
        if full_name in licenses:
            existing_license = licenses[full_name]
            if not existing_license.is_deprecated:
                continue

        licenses[full_name] = license

    # Add a Proprietary license for non-standard licenses
    licenses["proprietary"] = License("Proprietary", "Proprietary", False, False)

    return licenses


if __name__ == "__main__":
    from .updater import Updater

    updater = Updater()
    updater.dump()
