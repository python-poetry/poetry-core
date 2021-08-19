import logging
import re
import shutil
import sys
import tempfile
import warnings

from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import ContextManager
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union


if TYPE_CHECKING:
    from poetry.core.poetry import Poetry  # noqa


AUTHOR_REGEX = re.compile(r"(?u)^(?P<name>[- .,\w\d'’\"()]+) <(?P<email>.+?)>$")

METADATA_BASE = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
Summary: {summary}
"""

logger = logging.getLogger(__name__)


class Builder(object):
    format: Optional[str] = None

    def __init__(
        self,
        poetry: "Poetry",
        ignore_packages_formats: bool = False,
        executable: Optional[Union[Path, str]] = None,
    ) -> None:
        from poetry.core.masonry.metadata import Metadata
        from poetry.core.masonry.utils.module import Module

        self._poetry = poetry
        self._package = poetry.package
        self._path = poetry.file.parent
        self._excluded_files: Optional[Set[str]] = None
        self._executable = Path(executable or sys.executable)

        packages = []
        for p in self._package.packages:
            formats = p.get("format") or None

            # Default to including the package in both sdist & wheel
            # if the `format` key is not provided in the inline include table.
            if formats is None:
                formats = ["sdist", "wheel"]

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

        includes = []
        for include in self._package.include:
            formats = include.get("format", [])

            if (
                formats
                and self.format
                and self.format not in formats
                and not ignore_packages_formats
            ):
                continue

            includes.append(include)

        self._module = Module(
            self._package.name,
            self._path.as_posix(),
            packages=packages,
            includes=includes,
        )

        self._meta = Metadata.from_package(self._package)

    @property
    def executable(self) -> Path:
        return self._executable

    def build(self) -> None:
        raise NotImplementedError()

    def find_excluded_files(self) -> Set[str]:
        if self._excluded_files is None:
            from poetry.core.vcs import get_vcs

            # Checking VCS
            vcs = get_vcs(self._path)
            if not vcs:
                vcs_ignored_files = set()
            else:
                vcs_ignored_files = set(vcs.get_ignored_files())

            explicitely_excluded = set()
            for excluded_glob in self._package.exclude:
                for excluded in self._path.glob(str(excluded_glob)):
                    explicitely_excluded.add(
                        Path(excluded).relative_to(self._path).as_posix()
                    )

            explicitely_included = set()
            for inc in self._package.include:
                included_glob = inc["path"]
                for included in self._path.glob(str(included_glob)):
                    explicitely_included.add(
                        Path(included).relative_to(self._path).as_posix()
                    )

            ignored = (vcs_ignored_files | explicitely_excluded) - explicitely_included
            result = set()
            for file in ignored:
                result.add(file)

            # The list of excluded files might be big and we will do a lot
            # containment check (x in excluded).
            # Returning a set make those tests much much faster.
            self._excluded_files = result

        return self._excluded_files

    def is_excluded(self, filepath: Union[str, Path]) -> bool:
        exclude_path = Path(filepath)

        while True:
            if exclude_path.as_posix() in self.find_excluded_files():
                return True

            if len(exclude_path.parts) > 1:
                exclude_path = exclude_path.parent
            else:
                break

        return False

    def find_files_to_add(self, exclude_build: bool = True) -> Set["BuildIncludeFile"]:
        """
        Finds all files to add to the tarball
        """
        from poetry.core.masonry.utils.package_include import PackageInclude

        to_add = set()

        for include in self._module.includes:
            include.refresh()
            formats = include.formats or ["sdist"]

            for file in include.elements:
                if "__pycache__" in str(file):
                    continue

                if file.is_dir():
                    if self.format in formats:
                        for current_file in file.glob("**/*"):
                            include_file = BuildIncludeFile(
                                path=current_file,
                                project_root=self._path,
                                source_root=self._path,
                            )

                            if not current_file.is_dir() and not self.is_excluded(
                                include_file.relative_to_source_root()
                            ):
                                to_add.add(include_file)
                    continue

                if (
                    isinstance(include, PackageInclude)
                    and include.source
                    and self.format == "wheel"
                ):
                    source_root = include.base
                else:
                    source_root = self._path

                include_file = BuildIncludeFile(
                    path=file, project_root=self._path, source_root=source_root
                )

                if self.is_excluded(
                    include_file.relative_to_project_root()
                ) and isinstance(include, PackageInclude):
                    continue

                if file.suffix == ".pyc":
                    continue

                if file in to_add:
                    # Skip duplicates
                    continue

                logger.debug("Adding: {}".format(str(file)))
                to_add.add(include_file)

        # add build script if it is specified and explicitly required
        if self._package.build_script and not exclude_build:
            to_add.add(
                BuildIncludeFile(
                    path=self._package.build_script,
                    project_root=self._path,
                    source_root=self._path,
                )
            )

        return to_add

    def get_metadata_content(self) -> str:
        content = METADATA_BASE.format(
            name=self._meta.name,
            version=self._meta.version,
            summary=str(self._meta.summary),
        )

        # Optional fields
        if self._meta.home_page:
            content += "Home-page: {}\n".format(self._meta.home_page)

        if self._meta.license:
            content += "License: {}\n".format(self._meta.license)

        if self._meta.keywords:
            content += "Keywords: {}\n".format(self._meta.keywords)

        if self._meta.author:
            content += "Author: {}\n".format(str(self._meta.author))

        if self._meta.author_email:
            content += "Author-email: {}\n".format(str(self._meta.author_email))

        if self._meta.maintainer:
            content += "Maintainer: {}\n".format(str(self._meta.maintainer))

        if self._meta.maintainer_email:
            content += "Maintainer-email: {}\n".format(str(self._meta.maintainer_email))

        if self._meta.requires_python:
            content += "Requires-Python: {}\n".format(self._meta.requires_python)

        for classifier in self._meta.classifiers:
            content += "Classifier: {}\n".format(classifier)

        for extra in sorted(self._meta.provides_extra):
            content += "Provides-Extra: {}\n".format(extra)

        for dep in sorted(self._meta.requires_dist):
            content += "Requires-Dist: {}\n".format(dep)

        for url in sorted(self._meta.project_urls, key=lambda u: u[0]):
            content += "Project-URL: {}\n".format(str(url))

        if self._meta.description_content_type:
            content += "Description-Content-Type: {}\n".format(
                self._meta.description_content_type
            )

        if self._meta.description is not None:
            content += "\n" + str(self._meta.description) + "\n"

        return content

    def convert_entry_points(self) -> Dict[str, List[str]]:
        result = defaultdict(list)

        # Scripts -> Entry points
        for name, specification in self._poetry.local_config.get("scripts", {}).items():
            if isinstance(specification, str):
                # TODO: deprecate this in favour or reference
                specification = {"reference": specification, "type": "console"}

            if "callable" in specification:
                warnings.warn(
                    f"Use of callable in script specification ({name}) is deprecated. Use reference instead.",
                    DeprecationWarning,
                )
                specification = {
                    "reference": specification["callable"],
                    "type": "console",
                }

            if specification.get("type") != "console":
                continue

            extras = specification.get("extras", [])
            extras = f"[{', '.join(extras)}]" if extras else ""
            reference = specification.get("reference")

            if reference:
                result["console_scripts"].append(f"{name} = {reference}{extras}")

        # Plugins -> entry points
        plugins = self._poetry.local_config.get("plugins", {})
        for groupname, group in plugins.items():
            for name, specification in sorted(group.items()):
                result[groupname].append(f"{name} = {specification}")

        for groupname in result:
            result[groupname] = sorted(result[groupname])

        return dict(result)

    def convert_script_files(self) -> List[Path]:
        script_files: List[Path] = []

        for name, specification in self._poetry.local_config.get("scripts", {}).items():
            if isinstance(specification, dict) and specification.get("type") == "file":
                source = specification["reference"]

                if Path(source).is_absolute():
                    raise RuntimeError(
                        f"{source} in {name} is an absolute path. Expected relative path."
                    )

                abs_path = Path.joinpath(self._path, source)

                if not abs_path.exists():
                    raise RuntimeError(
                        f"{abs_path} in script specification ({name}) is not found."
                    )

                if not abs_path.is_file():
                    raise RuntimeError(
                        f"{abs_path} in script specification ({name}) is not a file."
                    )

                script_files.append(abs_path)

        return script_files

    @classmethod
    def convert_author(cls, author: str) -> Dict[str, str]:
        m = AUTHOR_REGEX.match(author)

        name = m.group("name")
        email = m.group("email")

        return {"name": name, "email": email}

    @classmethod
    @contextmanager
    def temporary_directory(cls, *args: Any, **kwargs: Any) -> ContextManager[str]:
        try:
            from tempfile import TemporaryDirectory

            with TemporaryDirectory(*args, **kwargs) as name:
                yield name
        except ImportError:
            name = tempfile.mkdtemp(*args, **kwargs)

            yield name

            shutil.rmtree(name)


class BuildIncludeFile:
    def __init__(
        self,
        path: Union[Path, str],
        project_root: Union[Path, str],
        source_root: Optional[Union[Path, str]] = None,
    ):
        """
        :param project_root: the full path of the project's root
        :param path: a full path to the file to be included
        :param source_root: the root path to resolve to
        """
        self.path = Path(path)
        self.project_root = Path(project_root).resolve()
        self.source_root = None if not source_root else Path(source_root).resolve()
        if not self.path.is_absolute() and self.source_root:
            self.path = self.source_root / self.path
        else:
            self.path = self.path

        try:
            self.path = self.path.resolve()
        except FileNotFoundError:
            # this is an issue in in python 3.5, since resolve uses strict=True by
            # default, this workaround needs to be maintained till python 2.7 and
            # python 3.5 are dropped, until we can use resolve(strict=False).
            pass

    def __eq__(self, other: Union["BuildIncludeFile", Path]) -> bool:
        if hasattr(other, "path"):
            return self.path == other.path

        return self.path == other

    def __ne__(self, other: Union["BuildIncludeFile", Path]) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.path)

    def __repr__(self) -> str:
        return str(self.path)

    def relative_to_project_root(self) -> Path:
        return self.path.relative_to(self.project_root)

    def relative_to_source_root(self) -> Path:
        if self.source_root is not None:
            return self.path.relative_to(self.source_root)

        return self.path
