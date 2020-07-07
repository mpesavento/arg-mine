"""Utility methods"""
from typing import List, Type, Optional  # noqa: F401
import datetime
import hashlib
import logging

LOG_FMT = "%(levelname)s:%(asctime)s:%(name)s: %(message)s"

_logger: Optional[logging.Logger] = None

# registry of loggers used in get_logger
loggers = {}


def get_logger(name, level=logging.INFO):
    global loggers

    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(LOG_FMT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        loggers[name] = logger

        return logger


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


def dataclasses_to_dicts(data):
    """    Converts a list of dataclass instances to a list of dictionaries
    Parameters
    ----------
    data : List[Type[dataclass]]
    Returns
    --------
    list_dict : List[dict]
    Examples
    --------
    >>> @dataclass
    >>> class Point:
    ...     x: int
    ...     y: int
    >>> dataclasses_to_dicts([Point(1,2), Point(2,3)])
    [{"x":1,"y":2},{"x":2,"y":3}]
    """
    from dataclasses import asdict

    return list(map(asdict, data))
