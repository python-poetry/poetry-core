from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.directory_dependency import DirectoryDependency
    from poetry.core.packages.file_dependency import FileDependency
    from poetry.core.packages.url_dependency import URLDependency
    from poetry.core.packages.vcs_dependency import VCSDependency

    DependencyTypes = Union[
        Dependency, DirectoryDependency, FileDependency, URLDependency, VCSDependency
    ]
