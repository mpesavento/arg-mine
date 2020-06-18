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


class ArgumenTextGatewayError(Error):
    """Base class for gateway parsing errors (400)"""

    def __init__(self, message):
        self.message = message


class Refused(ArgumenTextGatewayError):
    """
    Raise if source URL is responding with 404
    Filters 400 error message containing TARGET_MSG
    """
    TARGET_MSG = "Website could not be crawled"
