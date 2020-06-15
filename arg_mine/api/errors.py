"""
Errors for handling API
"""


class Error(Exception):
    pass


class Unavailable(Error):
    pass


class ArgMineGatewayError(Error):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class Refused(ArgMineGatewayError):
    pass