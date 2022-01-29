from __future__ import annotations

from typing import TYPE_CHECKING

from poetry.core.utils.helpers import readme_content_type


if TYPE_CHECKING:
    from poetry.core.packages.package import Package


class Metadata:

    metadata_version = "2.1"
    # version 1.0
    name = None
    version: str
    platforms = ()
    supported_platforms = ()
    summary = None
    description = None
    keywords = None
    home_page = None
    download_url = None
    author = None
    author_email = None
    license = None
    # version 1.1
    classifiers: tuple[str, ...] = ()
    requires = ()
    provides = ()
    obsoletes = ()
    # version 1.2
    maintainer = None
    maintainer_email = None
    requires_python = None
    requires_external = ()
    requires_dist: list[str] = []
    provides_dist = ()
    obsoletes_dist = ()
    project_urls: tuple[str, ...] = ()

    # Version 2.1
    description_content_type = None
    provides_extra: list[str] = []

    @classmethod
    def from_package(cls, package: Package) -> Metadata:
        from poetry.core.utils.helpers import canonicalize_name
        from poetry.core.utils.helpers import normalize_version
        from poetry.core.version.helpers import format_python_constraint

        meta = cls()

        meta.name = canonicalize_name(package.name)
        meta.version = normalize_version(package.version.text)
        meta.summary = package.description
        if package.readmes:
            descriptions = []
            for readme in package.readmes:
                with readme.open(encoding="utf-8") as f:
                    descriptions.append(f.read())
            meta.description = "\n".join(descriptions)

        meta.keywords = ",".join(package.keywords)
        meta.home_page = package.homepage or package.repository_url
        meta.author = package.author_name
        meta.author_email = package.author_email

        if package.license:
            meta.license = package.license.id

        meta.classifiers = tuple(package.all_classifiers)

        # Version 1.2
        meta.maintainer = package.maintainer_name
        meta.maintainer_email = package.maintainer_email

        # Requires python
        if package.python_versions != "*":
            meta.requires_python = format_python_constraint(package.python_constraint)

        meta.requires_dist = [d.to_pep_508() for d in package.requires]

        # Version 2.1
        if package.readmes:
            meta.description_content_type = readme_content_type(package.readmes[0])

        meta.provides_extra = list(package.extras)

        if package.urls:
            for name, url in package.urls.items():
                if name == "Homepage" and meta.home_page == url:
                    continue

                meta.project_urls += (f"{name}, {url}",)

        return meta
