# -*- coding: utf-8 -*-
from poetry.core.pyproject import PyProjectTOMLFile


class TomlFile(PyProjectTOMLFile):
    @classmethod
    def __new__(cls, *args, **kwargs):
        import warnings

        warnings.warn(
            "Use of {}.{} has been deprecated, use {}.{} instead.".format(
                cls.__module__,
                cls.__name__,
                PyProjectTOMLFile.__module__,
                PyProjectTOMLFile.__name__,
            ),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return super(TomlFile, cls).__new__(cls)
