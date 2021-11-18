from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from poetry.core.semver.helpers import parse_constraint
from poetry.core.version.markers import parse_marker


if TYPE_CHECKING:
    from poetry.core.packages.types import DependencyTypes
    from poetry.core.semver.helpers import VersionTypes

from poetry.core.packages.package import Package
from poetry.core.packages.utils.utils import create_nested_marker


class ProjectPackage(Package):
    def __init__(
        self,
        name: str,
        version: Union[str, "VersionTypes"],
        pretty_version: Optional[str] = None,
    ) -> None:
        super().__init__(name, version, pretty_version)

        self.build_config = {}
        self.packages = []
        self.include = []
        self.exclude = []
        self.custom_urls = {}

        if self._python_versions == "*":
            self._python_constraint = parse_constraint("~2.7 || >=3.4")

    @property
    def build_script(self) -> Optional[str]:
        return self.build_config.get("script")

    def is_root(self) -> bool:
        return True

    def to_dependency(self) -> Union["DependencyTypes"]:
        dependency = super().to_dependency()

        dependency.is_root = True

        return dependency

    @property
    def python_versions(self) -> Union[str, "VersionTypes"]:
        return self._python_versions

    @python_versions.setter
    def python_versions(self, value: Union[str, "VersionTypes"]) -> None:
        from poetry.core.semver.version_range import VersionRange

        self._python_versions = value

        if value == "*" or value == VersionRange():
            value = "~2.7 || >=3.4"

        self._python_constraint = parse_constraint(value)
        self._python_marker = parse_marker(
            create_nested_marker("python_version", self._python_constraint)
        )

    @property
    def urls(self) -> Dict[str, Any]:
        urls = super().urls

        urls.update(self.custom_urls)

        return urls

    def build_should_generate_setup(self) -> bool:
        return self.build_config.get("generate-setup-file", True)
