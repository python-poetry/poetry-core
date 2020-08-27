from tomlkit.exceptions import TOMLKitError

from poetry.core.exceptions import PoetryCoreException


class TOMLError(TOMLKitError, PoetryCoreException):
    pass
