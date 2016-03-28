class PydmrsError(Exception):
    pass

class PydmrsTypeError(PydmrsError, TypeError):
    pass

class PydmrsValueError(PydmrsError, ValueError):
    pass

class PydmrsKeyError(PydmrsError, KeyError):
    pass

class PydmrsWarning(PydmrsError, Warning):
    pass

class PydmrsDeprecationWarning(PydmrsWarning, DeprecationWarning):
    pass