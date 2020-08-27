# -*- coding: utf-8 -*-
from poetry.core.toml import TOMLFile


class TomlFile(TOMLFile):
    @classmethod
    def __new__(cls, *args, **kwargs):
        import warnings

        warnings.warn(
            "Use of {}.{} has been deprecated, use {}.{} instead.".format(
                cls.__module__, cls.__name__, TOMLFile.__module__, TOMLFile.__name__,
            ),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return super(TomlFile, cls).__new__(cls)
