"""
Errors for handling API
"""


class Error(Exception):
    """Base class for a generic error"""
    pass


class Unavailable(Error):
    """Server returns an HTTPError other than 400"""
    pass


class ArgumenTextGatewayError(Error):
    """Base class for gateway parsing errors (400)"""
    def __init__(self, code, message):
        self.code = code
        self.message = message


class Refused(ArgumenTextGatewayError):
    """Raise if 400 output code is ==1 (Not implemented in server currently)"""
    pass
