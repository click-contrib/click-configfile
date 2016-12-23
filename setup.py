# -*- coding: utf-8 -*
"""
Setup script for click-configfile.

USAGE:
    python setup.py install
"""

from __future__ import print_function
import sys
import os.path

HERE0 = os.path.dirname(__file__) or os.curdir
os.chdir(HERE0)
HERE = os.curdir
sys.path.insert(0, HERE)

from setuptools import find_packages, setup
import inspect
# MAYBE: from setuptools_behave import behave_test

# -----------------------------------------------------------------------------
# UTILITY:
# -----------------------------------------------------------------------------
def find_packages_by_root_package(where):
    """Better than excluding everything that is not needed,
    collect only what is needed.
    """
    root_package = os.path.basename(where)
    packages = [ "%s.%s" % (root_package, sub_package)
                 for sub_package in find_packages(where)]
    packages.insert(0, root_package)
    return packages

def make_long_description(marker=None, intro=None):
    """
    click_ is a framework to simplify writing composable commands for
    command-line tools. This package extends the click_ functionality
    by adding support for commands that use configuration files.

    .. _click: https://click.pocoo.org/

    EXAMPLE:

    A configuration file, like:

    .. code-block:: INI

        # -- FILE: foo.ini
        [foo]
        flag = yes
        name = Alice and Bob
        numbers = 1 4 9 16 25
        filenames = foo/xxx.txt
            bar/baz/zzz.txt

        [person.alice]
        name = Alice
        birthyear = 1995

        [person.bob]
        name = Bob
        birthyear = 2001

    can be processed with:

    .. code-block:: python

        # EXAMPLE:
    """
    if intro is None:
        intro = inspect.getdoc(make_long_description)

    with open("README.rst", "r") as infile:
        line = infile.readline()
        while not line.strip().startswith(marker):
            line = infile.readline()

        # -- COLLECT REMAINING: Usage example
        contents = infile.read()

    text = intro +"\n" + contents
    return text

# -- FILE: example_command_with_configfile.py (ALL PARTS: simplified)

# ----------------------------------------------------------------------------
# PROJECT CONFIGURATION (for sdist/setup mostly):
# ----------------------------------------------------------------------------
package_version = "0.2.2"
description = """\
This package extends the `click <https://click.pocoo.org/>`_ functionality
by adding support for commands that use configuration files."""

install_requires = ["click >= 6.6", "six >= 1.10"]
before_py35_extra = []
if sys.version < "3.5":
    install_requires.append("configparser >= 3.5.0")
    before_py35_extra.append("configparser >= 3.5.0")

EXAMPLE_MARKER = "# MARKER-EXAMPLE:"
long_description = make_long_description(EXAMPLE_MARKER)
SETUP_DEBUG = os.environ.get("SETUP_DEBUG", "no") in ("yes", "true", "on")
if SETUP_DEBUG:
    print(long_description)


# -----------------------------------------------------------------------------
# SETUP:
# -----------------------------------------------------------------------------
setup(
    name="click-configfile",
    version=package_version,
    url="https://github.com/jenisys/click-configfile",
    download_url="https://pypi.python.org/pypi/click-configfile/%s" % package_version,
    author="Jens Engel",
    author_email="jenisys@noreply.github.com",
    license="BSD",
    description= "This package supports click commands that use configuration files.",
    long_description = long_description,
    keywords   = "click, configfile, configparser",
    platforms  = [ 'any' ],
    # packages = find_packages_by_root_package("click_configfile"),
    py_modules = ["click_configfile"],
    install_requires=install_requires,
    # BAD: setup_requires=["pytest-runner"],
    tests_require=["pytest >= 3.0", "pytest-runner"],
    include_package_data=True,
    extras_require={
        # -- SUPPORT-WHEELS: Extra packages for Python2.6 and ...
        # SEE: https://bitbucket.org/pypa/wheel/ , CHANGES.txt (v0.24.0)
        ':python_version=="2.6"': before_py35_extra,
        ':python_version=="2.7"': before_py35_extra,
        ':python_version=="3.3"': before_py35_extra,
        ':python_version=="3.4"': before_py35_extra,
    },
    zip_safe=True,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
