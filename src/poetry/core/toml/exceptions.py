from tomlkit.exceptions import TOMLKitError

from poetry.core.exceptions import PoetryCoreError


class TOMLError(TOMLKitError, PoetryCoreError):
    pass
