# -*- coding: utf-8 -*
"""
Setup script for click-configfile.

USAGE:
    python setup.py install
"""

import sys
import os.path

HERE0 = os.path.dirname(__file__) or os.curdir
os.chdir(HERE0)
HERE = os.curdir
sys.path.insert(0, HERE)

from setuptools import find_packages, setup
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


# ----------------------------------------------------------------------------
# PROJECT CONFIGURATION (for sdist/setup mostly):
# ----------------------------------------------------------------------------
install_requires = [ "click >= 6.6" ]
before_py35_extra = []
if sys.version < "3.5":
    install_requires.append("configparser")
    before_py35_extra.append("configparser")

README = os.path.join(HERE, "README.rst")
long_description = "".join(open(README).readlines()[4:])

NAME = "click-configfile"
CLASSIFIERS = """\
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
Intended Audience :: System Administrators
License :: OSI Approved :: BSD License
Natural Language :: English
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Utilities
"""

# -----------------------------------------------------------------------------
# SETUP:
# -----------------------------------------------------------------------------
setup(
    name="click-configfile",
    version="0.1.0",
    url="http://pypi.python.org/pypi/click-configfile/",
    author="Jens Engel",
    author_email="jenisys@noreply.github.com",
    license="BSD",
    description= """\
This package extends the 'click' functionality by adding support for commands
that use configuration files.""",
    long_description = long_description,
    keywords   = "click, configfile, configparser",
    platforms  = [ 'any' ],
    classifiers= CLASSIFIERS.splitlines(),
    # packages = find_packages_by_root_package("click_configfile"),
    modules = ["click_configfile"],
    install_requires=install_requires,
    include_package_data=True,
    extras_require={
        # -- SUPPORT-WHEELS: Extra packages for Python2.6
        # SEE: https://bitbucket.org/pypa/wheel/ , CHANGES.txt (v0.24.0)
        ':python_version=="2.6"': before_py35_extra,
        ':python_version=="2.7"': before_py35_extra,
        ':python_version=="3.3"': before_py35_extra,
        ':python_version=="3.4"': before_py35_extra,
    },
)
