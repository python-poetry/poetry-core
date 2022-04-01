"""
PEP-517 compliant buildsystem API
"""
from __future__ import annotations

import logging

from pathlib import Path
from typing import Any

from poetry.core.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.wheel import WheelBuilder


log = logging.getLogger(__name__)


def get_requires_for_build_wheel(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    """
    Returns an additional list of requirements for building, as PEP508 strings,
    above and beyond those specified in the pyproject.toml file.

    This implementation is optional. At the moment it only returns an empty list, which would be the same as if
    not define. So this is just for completeness for future implementation.
    """

    return []


# For now, we require all dependencies to build either a wheel or an sdist.
get_requires_for_build_sdist = get_requires_for_build_wheel


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    poetry = Factory().create_poetry(Path(".").resolve(), with_groups=False)
    builder = WheelBuilder(poetry)

    dist_info = Path(metadata_directory, builder.dist_info)
    dist_info.mkdir(parents=True, exist_ok=True)

    if "scripts" in poetry.local_config or "plugins" in poetry.local_config:
        with (dist_info / "entry_points.txt").open("w", encoding="utf-8") as f:
            builder._write_entry_points(f)

    with (dist_info / "WHEEL").open("w", encoding="utf-8") as f:
        builder._write_wheel_file(f)

    with (dist_info / "METADATA").open("w", encoding="utf-8") as f:
        builder._write_metadata_file(f)

    return dist_info.name


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Builds a wheel, places it in wheel_directory"""
    poetry = Factory().create_poetry(Path(".").resolve(), with_groups=False)

    return WheelBuilder.make_in(poetry, Path(wheel_directory))


def build_sdist(
    sdist_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    """Builds an sdist, places it in sdist_directory"""
    poetry = Factory().create_poetry(Path(".").resolve(), with_groups=False)

    path = SdistBuilder(poetry).build(Path(sdist_directory))

    return path.name


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    poetry = Factory().create_poetry(Path(".").resolve(), with_groups=False)

    return WheelBuilder.make_in(poetry, Path(wheel_directory), editable=True)


get_requires_for_build_editable = get_requires_for_build_wheel
prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel
