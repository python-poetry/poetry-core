from __future__ import absolute_import
from __future__ import unicode_literals

from typing import Dict
from typing import List
from typing import Optional

from .json import validate_object
from .packages.dependency import Dependency
from .packages.project_package import ProjectPackage
from .poetry import Poetry
from .spdx import license_by_id
from .utils._compat import Path
from .utils.toml_file import TomlFile


class Factory(object):
    """
    Factory class to create various elements needed by Poetry.
    """

    def create_poetry(self, cwd=None):  # type: (Optional[Path]) -> Poetry
        poetry_file = self.locate(cwd)

        local_config = TomlFile(poetry_file.as_posix()).read()
        if "tool" not in local_config or "poetry" not in local_config["tool"]:
            raise RuntimeError(
                "[tool.poetry] section not found in {}".format(poetry_file.name)
            )
        local_config = local_config["tool"]["poetry"]

        # Checking validity
        check_result = self.validate(local_config)
        if check_result["errors"]:
            message = ""
            for error in check_result["errors"]:
                message += "  - {}\n".format(error)

            raise RuntimeError("The Poetry configuration is invalid:\n" + message)

        # Load package
        name = local_config["name"]
        version = local_config["version"]
        package = ProjectPackage(name, version, version)
        package.root_dir = poetry_file.parent

        for author in local_config["authors"]:
            package.authors.append(author)

        for maintainer in local_config.get("maintainers", []):
            package.maintainers.append(maintainer)

        package.description = local_config.get("description", "")
        package.homepage = local_config.get("homepage")
        package.repository_url = local_config.get("repository")
        package.documentation_url = local_config.get("documentation")
        try:
            license_ = license_by_id(local_config.get("license", ""))
        except ValueError:
            license_ = None

        package.license = license_
        package.keywords = local_config.get("keywords", [])
        package.classifiers = local_config.get("classifiers", [])

        if "readme" in local_config:
            package.readme = Path(poetry_file.parent) / local_config["readme"]

        if "platform" in local_config:
            package.platform = local_config["platform"]

        if "dependencies" in local_config:
            for name, constraint in local_config["dependencies"].items():
                if name.lower() == "python":
                    package.python_versions = constraint
                    continue

                if isinstance(constraint, list):
                    for _constraint in constraint:
                        package.add_dependency(name, _constraint)

                    continue

                package.add_dependency(name, constraint)

        if "dev-dependencies" in local_config:
            for name, constraint in local_config["dev-dependencies"].items():
                if isinstance(constraint, list):
                    for _constraint in constraint:
                        package.add_dependency(name, _constraint, category="dev")

                    continue

                package.add_dependency(name, constraint, category="dev")

        extras = local_config.get("extras", {})
        for extra_name, requirements in extras.items():
            package.extras[extra_name] = []

            # Checking for dependency
            for req in requirements:
                req = Dependency(req, "*")

                for dep in package.requires:
                    if dep.name == req.name:
                        dep.in_extras.append(extra_name)
                        package.extras[extra_name].append(dep)

                        break

        if "build" in local_config:
            package.build = local_config["build"]

        if "include" in local_config:
            package.include = local_config["include"]

        if "exclude" in local_config:
            package.exclude = local_config["exclude"]

        if "packages" in local_config:
            package.packages = local_config["packages"]

        # Custom urls
        if "urls" in local_config:
            package.custom_urls = local_config["urls"]

        return Poetry(poetry_file, local_config, package)

    @classmethod
    def validate(
        cls, config, strict=False
    ):  # type: (dict, bool) -> Dict[str, List[str]]
        """
        Checks the validity of a configuration
        """
        result = {"errors": [], "warnings": []}
        # Schema validation errors
        validation_errors = validate_object(config, "poetry-schema")

        result["errors"] += validation_errors

        if strict:
            # If strict, check the file more thoroughly

            # Checking license
            license = config.get("license")
            if license:
                try:
                    license_by_id(license)
                except ValueError:
                    result["errors"].append("{} is not a valid license".format(license))

            if "dependencies" in config:
                python_versions = config["dependencies"]["python"]
                if python_versions == "*":
                    result["warnings"].append(
                        "A wildcard Python dependency is ambiguous. "
                        "Consider specifying a more explicit one."
                    )

                for name, constraint in config["dependencies"].items():
                    if not isinstance(constraint, dict):
                        continue

                    if "allows-prereleases" in constraint:
                        result["warnings"].append(
                            'The "{}" dependency specifies '
                            'the "allows-prereleases" property, which is deprecated. '
                            'Use "allow-prereleases" instead.'.format(name)
                        )

            # Checking for scripts with extras
            if "scripts" in config:
                scripts = config["scripts"]
                for name, script in scripts.items():
                    if not isinstance(script, dict):
                        continue

                    extras = script["extras"]
                    for extra in extras:
                        if extra not in config["extras"]:
                            result["errors"].append(
                                'Script "{}" requires extra "{}" which is not defined.'.format(
                                    name, extra
                                )
                            )

        return result

    @classmethod
    def locate(cls, cwd):  # type: (Path) -> Path
        candidates = [Path(cwd)]
        candidates.extend(Path(cwd).parents)

        for path in candidates:
            poetry_file = path / "pyproject.toml"

            if poetry_file.exists():
                return poetry_file

        else:
            raise RuntimeError(
                "Poetry could not find a pyproject.toml file in {} or its parents".format(
                    cwd
                )
            )
