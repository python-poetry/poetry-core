# Poetry Core
[![PyPI version](https://img.shields.io/pypi/v/poetry-core)](https://pypi.org/project/poetry-core/)
[![Python Versions](https://img.shields.io/pypi/pyversions/poetry-core)](https://pypi.org/project/poetry-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![](https://github.com/python-poetry/poetry-core/workflows/Tests/badge.svg)](https://github.com/python-poetry/poetry-core/actions?query=workflow%3ATests)

A [PEP 517](https://www.python.org/dev/peps/pep-0517/) build backend implementation developed for
[Poetry](https://github.com/python-poetry/poetry). This project is intended to be a light weight, fully compliant,
self-contained package allowing PEP 517 compatible build frontends to build Poetry managed projects.

## Usage
In most cases, the usage of this package is transparent to the end-user as it is either made use by Poetry itself
or a PEP 517 frontend (eg: `pip`).

In order to enable the use `poetry-core` as your build backend, the following snippet must be present in your
project's `pyproject.toml` file.

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Once this is present, a PEP 517 frontend like `pip` can build and install your project from source without the need
for Poetry or any of it's dependencies.

```shell
# install to current environment
pip install /path/to/poetry/managed/project

# build a wheel package
pip wheel /path/to/poetry/managed/project
```

## Why is this required?
Prior to the release of version `1.1.0`, Poetry was a build as a project management tool that included a PEP 517
build backend. This was inefficient and time consuming in majority cases a PEP 517 build was required. For example,
both `pip` and `tox` (with isolated builds) would install Poetry and all dependencies it required. Most of these
dependencies are not required when the objective is to simply build either a source or binary distribution of your
project.

In order to improve the above situation, `poetry-core` was created. Shared functionality pertaining to PEP 517 build
backends, including reading lock file, `pyproject.toml` and building wheel/sdist, were implemented in this package.  This
makes PEP 517 builds extremely fast for Poetry managed packages.
