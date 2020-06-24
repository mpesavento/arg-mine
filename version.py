"""
Holds the current version number
Uses standard semantic versioning: major.minor.bugfix
Increment the version for each update.
"""

_major_version = 0
_minor_version = 1
_bugfix_version = 0

__version__ = "{}.{}.{}".format(_major_version, _minor_version, _bugfix_version)

if __name__ == "__main__":
    print(__version__)