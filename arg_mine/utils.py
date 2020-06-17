"""Utility methods"""

import hashlib


def enum(**named_values):
    """
    Named enum. Doesnt need to use the Enum.NAME.value with the built in Enum

    Example
    -------
    >>> MY_CONSTANTS = enum(FOO="foo", BAR="bar")
    >>> MY_CONSTANTS.FOO
    "foo"

    Parameters
    ----------
    named_values: dict
        key is parameter name and value is parameter value (eg string)

    Returns
    -------
    Enum class
    """
    return type("Enum", (), named_values)


def unique_hash(input_str: str) -> str:
    """Uses MD5 to return a unique key, assuming the input string is unique"""
    # assuming default UTF-8
    return hashlib.md5(input_str.encode()).hexdigest()
