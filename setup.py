from setuptools import find_packages, setup


import codecs
import os
import re


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="arg_mine",
    packages=find_packages(),
    version=find_version("version.py"),
    description="Uses the ArgumentText API to mine arguments from selected data sources. A part of the Great American Debate project https://www.greatamericandebate.org/",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mpesavento/arg-mine",
    author="Mike Pesavento",
    author_email="mike@peztek.com",
    license="MIT",
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
)
