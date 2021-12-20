from typing import Any
from typing import Type

from poetry.core.toml import TOMLFile


class TomlFile(TOMLFile):
    @classmethod
    def __new__(cls: Type[TOMLFile], *args: Any, **kwargs: Any) -> TOMLFile:
        import warnings

        this_import = f"{cls.__module__}.{cls.__name__}"
        new_import = f"{TOMLFile.__module__}.{TOMLFile.__name__}"
        warnings.warn(
            f"Use of {this_import} has been deprecated, use {new_import} instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls)  # type: ignore[no-any-return,misc]
