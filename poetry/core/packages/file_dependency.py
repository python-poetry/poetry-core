import hashlib
import io

from poetry.core._vendor.pkginfo.distribution import HEADER_ATTRS
from poetry.core._vendor.pkginfo.distribution import HEADER_ATTRS_2_0

from poetry.core.packages.utils.utils import path_to_url
from poetry.core.utils._compat import Path

from .dependency import Dependency


# Patching pkginfo to support Metadata version 2.1 (PEP 566)
HEADER_ATTRS.update(
    {"2.1": HEADER_ATTRS_2_0 + (("Provides-Extra", "provides_extra", True),)}
)


class FileDependency(Dependency):
    def __init__(
        self,
        name,
        path,  # type: Path
        category="main",  # type: str
        optional=False,  # type: bool
        base=None,  # type: Path
    ):
        self._path = path
        self._base = base
        self._full_path = path

        if self._base and not self._path.is_absolute():
            self._full_path = self._base / self._path

        if not self._full_path.exists():
            raise ValueError("File {} does not exist".format(self._path))

        if self._full_path.is_dir():
            raise ValueError("{} is a directory, expected a file".format(self._path))

        super(FileDependency, self).__init__(
            name, "*", category=category, optional=optional, allows_prereleases=True
        )

    @property
    def path(self):
        return self._path

    @property
    def full_path(self):
        return self._full_path.resolve()

    def is_file(self):
        return True

    def hash(self):
        h = hashlib.sha256()
        with self._full_path.open("rb") as fp:
            for content in iter(lambda: fp.read(io.DEFAULT_BUFFER_SIZE), b""):
                h.update(content)

        return h.hexdigest()

    @property
    def base_pep_508_name(self):  # type: () -> str
        requirement = self.pretty_name

        if self.extras:
            requirement += "[{}]".format(",".join(self.extras))

        path = path_to_url(self.path) if self.path.is_absolute() else self.path
        requirement += " @ {}".format(path)

        return requirement
