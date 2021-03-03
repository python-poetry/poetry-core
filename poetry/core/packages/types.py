from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:
    from .dependency import Dependency
    from .directory_dependency import DirectoryDependency
    from .file_dependency import FileDependency
    from .url_dependency import URLDependency
    from .vcs_dependency import VCSDependency

    DependencyTypes = Union[
        Dependency, DirectoryDependency, FileDependency, URLDependency, VCSDependency
    ]
