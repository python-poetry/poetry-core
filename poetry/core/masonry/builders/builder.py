# -*- coding: utf-8 -*-
import logging
import re
import shutil
import tempfile

from collections import defaultdict
from contextlib import contextmanager
from typing import Set
from typing import Union

from poetry.core.utils._compat import Path
from poetry.core.utils._compat import to_str
from poetry.core.vcs import get_vcs

from ..metadata import Metadata
from ..utils.module import Module
from ..utils.package_include import PackageInclude


AUTHOR_REGEX = re.compile(r"(?u)^(?P<name>[- .,\w\d'’\"()]+) <(?P<email>.+?)>$")

METADATA_BASE = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
Summary: {summary}
"""

logger = logging.getLogger(__name__)


class Builder(object):
    AVAILABLE_PYTHONS = {"2", "2.7", "3", "3.4", "3.5", "3.6", "3.7"}

    format = None

    def __init__(
        self, poetry, ignore_packages_formats=False
    ):  # type: ("Poetry", bool) -> None
        self._poetry = poetry
        self._package = poetry.package
        self._path = poetry.file.parent
        self._original_path = self._path
        self._excluded_files = None

        packages = []
        for p in self._package.packages:
            formats = p.get("format", [])
            if not isinstance(formats, list):
                formats = [formats]

            if (
                formats
                and self.format
                and self.format not in formats
                and not ignore_packages_formats
            ):
                continue

            packages.append(p)

        self._module = Module(
            self._package.name,
            self._path.as_posix(),
            packages=packages,
            includes=self._package.include,
        )
        self._meta = Metadata.from_package(self._package)

    def build(self):
        raise NotImplementedError()

    def find_excluded_files(self):  # type: () -> Set[str]
        if self._excluded_files is None:
            # Checking VCS
            vcs = get_vcs(self._original_path)
            if not vcs:
                vcs_ignored_files = set()
            else:
                vcs_ignored_files = set(vcs.get_ignored_files())

            explicitely_excluded = set()
            for excluded_glob in self._package.exclude:
                for excluded in self._path.glob(excluded_glob):
                    explicitely_excluded.add(
                        Path(excluded).relative_to(self._path).as_posix()
                    )

            ignored = vcs_ignored_files | explicitely_excluded
            result = set()
            for file in ignored:
                result.add(file)

            # The list of excluded files might be big and we will do a lot
            # containment check (x in excluded).
            # Returning a set make those tests much much faster.
            self._excluded_files = result

        return self._excluded_files

    def is_excluded(self, filepath):  # type: (Union[str, Path]) -> bool
        exclude_path = Path(filepath)

        while True:
            if exclude_path.as_posix() in self.find_excluded_files():
                return True

            if len(exclude_path.parts) > 1:
                exclude_path = exclude_path.parent
            else:
                break

        return False

    def find_files_to_add(self, exclude_build=True):  # type: (bool) -> list
        """
        Finds all files to add to the tarball
        """
        to_add = []

        for include in self._module.includes:
            for file in include.elements:
                if "__pycache__" in str(file):
                    continue

                if file.is_dir():
                    continue

                file = file.relative_to(self._path)

                if self.is_excluded(file) and isinstance(include, PackageInclude):
                    continue

                if file.suffix == ".pyc":
                    continue

                if file in to_add:
                    # Skip duplicates
                    continue

                logger.debug(" - Adding: {}".format(str(file)))
                to_add.append(file)

        # Include project files
        logger.debug(" - Adding: pyproject.toml")
        to_add.append(Path("pyproject.toml"))

        # If a license file exists, add it
        for license_file in self._path.glob("LICENSE*"):
            logger.debug(" - Adding: {}".format(license_file.relative_to(self._path)))
            to_add.append(license_file.relative_to(self._path))

        # If a README is specified we need to include it
        # to avoid errors
        if "readme" in self._poetry.local_config:
            readme = self._path / self._poetry.local_config["readme"]
            if readme.exists():
                logger.debug(" - Adding: {}".format(readme.relative_to(self._path)))
                to_add.append(readme.relative_to(self._path))

        # If a build script is specified and explicitely required
        # we add it to the list of files
        if self._package.build_script and not exclude_build:
            to_add.append(Path(self._package.build_script))

        return sorted(to_add)

    def get_metadata_content(self):  # type: () -> bytes
        content = METADATA_BASE.format(
            name=self._meta.name,
            version=self._meta.version,
            summary=to_str(self._meta.summary),
        )

        # Optional fields
        if self._meta.home_page:
            content += "Home-page: {}\n".format(self._meta.home_page)

        if self._meta.license:
            content += "License: {}\n".format(self._meta.license)

        if self._meta.keywords:
            content += "Keywords: {}\n".format(self._meta.keywords)

        if self._meta.author:
            content += "Author: {}\n".format(to_str(self._meta.author))

        if self._meta.author_email:
            content += "Author-email: {}\n".format(to_str(self._meta.author_email))

        if self._meta.maintainer:
            content += "Maintainer: {}\n".format(to_str(self._meta.maintainer))

        if self._meta.maintainer_email:
            content += "Maintainer-email: {}\n".format(
                to_str(self._meta.maintainer_email)
            )

        if self._meta.requires_python:
            content += "Requires-Python: {}\n".format(self._meta.requires_python)

        for classifier in self._meta.classifiers:
            content += "Classifier: {}\n".format(classifier)

        for extra in sorted(self._meta.provides_extra):
            content += "Provides-Extra: {}\n".format(extra)

        for dep in sorted(self._meta.requires_dist):
            content += "Requires-Dist: {}\n".format(dep)

        for url in sorted(self._meta.project_urls, key=lambda u: u[0]):
            content += "Project-URL: {}\n".format(to_str(url))

        if self._meta.description_content_type:
            content += "Description-Content-Type: {}\n".format(
                self._meta.description_content_type
            )

        if self._meta.description is not None:
            content += "\n" + to_str(self._meta.description) + "\n"

        return content

    def convert_entry_points(self):  # type: () -> dict
        result = defaultdict(list)

        # Scripts -> Entry points
        for name, ep in self._poetry.local_config.get("scripts", {}).items():
            extras = ""
            if isinstance(ep, dict):
                extras = "[{}]".format(", ".join(ep["extras"]))
                ep = ep["callable"]

            result["console_scripts"].append("{} = {}{}".format(name, ep, extras))

        # Plugins -> entry points
        plugins = self._poetry.local_config.get("plugins", {})
        for groupname, group in plugins.items():
            for name, ep in sorted(group.items()):
                result[groupname].append("{} = {}".format(name, ep))

        for groupname in result:
            result[groupname] = sorted(result[groupname])

        return dict(result)

    @classmethod
    def convert_author(cls, author):  # type: (...) -> dict
        m = AUTHOR_REGEX.match(author)

        name = m.group("name")
        email = m.group("email")

        return {"name": name, "email": email}

    @classmethod
    @contextmanager
    def temporary_directory(cls, *args, **kwargs):
        try:
            from tempfile import TemporaryDirectory

            with TemporaryDirectory(*args, **kwargs) as name:
                yield name
        except ImportError:
            name = tempfile.mkdtemp(*args, **kwargs)

            yield name

            shutil.rmtree(name)
