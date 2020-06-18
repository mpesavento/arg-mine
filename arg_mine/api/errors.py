"""
Errors for handling API
"""


class Error(Exception):
    """Base class for a generic error"""

    pass


class Unavailable(Error):
    """Server returns an HTTPError other than 400"""

    pass


class NotResponding(Error):
    """ConnectionError or Timeout"""
    pass


class ArgumenTextGatewayError(Error):
    """Base class for gateway parsing errors (400)"""

    def __init__(self, code, message):
        self.message = message
        self.code = code

    def __str__(self):
        return "{}: {}: {}".format(self.__class__.__name__, self.code, self.message)


class Refused(ArgumenTextGatewayError):
    """
    Raise if source URL is responding with 404
    Filters 400 error message containing TARGET_MSG
    """
    TARGET_MSG = "Website could not be crawled"
    pass


class InternalGatewayError(ArgumenTextGatewayError):
    """Raise if get 500, often get this if have bad json parameters"""
    pass
