# Contributing

## Setup

1. Install and configured Python versions however is appropriate for your operating system
   (try [`pyenv`](https://github.com/pyenv/pyenv)).
2. Ensure you are working with the latest release version of Poetry, to start. 
   Follow the instructions the installer outputs in order to ensure that `poetry` is on your `PATH`.

       curl -sL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

3. Install dependencies

       poetry install

4. Run tests

       poetry run tox

5. If all tests pass for all Python versions, you're in great shape!
   If tests pass for just one and not the others because you've not installed that Python version, you're
   probably OK, but keep an eye out for problems when you submit the PR.

6. Install the git pre-commit hooks with [`pre-commit`](https://pre-commit.com/):

       pre-commit install --install-hooks
