from typing import Dict
from typing import List
from typing import Union

from poetry.core.utils.helpers import readme_content_type


Result = Dict[str, List[str]]


def _dependencies(deps: dict) -> Result:
    result: Result = {"errors": [], "warnings": []}

    python_versions = deps["python"]
    if python_versions == "*":
        result["warnings"].append(
            "A wildcard Python dependency is ambiguous. "
            "Consider specifying a more explicit one."
        )

    for name, constraint in deps.items():
        if not isinstance(constraint, dict):
            continue

        if "allows-prereleases" in constraint:
            result["warnings"].append(
                f'The "{name}" dependency specifies '
                'the "allows-prereleases" property, which is deprecated. '
                'Use "allow-prereleases" instead.'
            )

    return result


def _scripts(scripts: dict, extras: List[str]) -> Result:
    result: Result = {"errors": [], "warnings": []}

    for name, script in scripts.items():
        if not isinstance(script, dict):
            continue

        for e in script["extras"]:
            if e not in extras:
                result["errors"].append(
                    f'Script "{name}" requires extra "{e}" which is not defined.'
                )
    return result


def _readme(readme: Union[str, List[str]]) -> Result:
    result: Result = {"errors": [], "warnings": []}

    if not isinstance(readme, str):
        readme_types = {readme_content_type(r) for r in readme}
        if len(readme_types) > 1:
            result["errors"].append(
                f"Declared README files must be of same type: found {', '.join(sorted(readme_types))}"
            )

    return result


def strict(config: dict) -> Result:

    result: Result = {"errors": [], "warnings": []}

    def extend_result(total: Result, result: Result) -> None:
        for key in ["warnings", "errors"]:
            total[key].extend(result[key])

    if "dependencies" in config:
        extend_result(result, _dependencies(config["dependencies"]))

    # Checking for scripts with extras
    if "scripts" in config:
        extend_result(result, _scripts(config["scripts"], config["extras"]))

    # Checking types of all readme files (must match)
    if "readme" in config:
        extend_result(result, _readme(config["readme"]))

    return result
