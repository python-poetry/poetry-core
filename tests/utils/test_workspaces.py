from __future__ import annotations

import tomlkit

import poetry.core.utils.workspaces


def test_is_poetry_workspace() -> None:
    content = """[tool.poetry.workspace]"""
    data = tomlkit.parse(content)

    res = poetry.core.utils.workspaces.is_poetry_workspace(data)

    assert res is True


def test_is_poetry_workspace_should_return_false_when_missing_keys() -> None:
    content = """[tool.other]"""
    data = tomlkit.parse(content)

    res = poetry.core.utils.workspaces.is_poetry_workspace(data)

    assert res is False
