# -*- coding: UTF-8 -*-
"""
Unit tests for :class:`click_configfile.ConfigFileReader`.
"""

from __future__ import absolute_import
import os.path


# -----------------------------------------------------------------------------
# TEST SUPPORT
# -----------------------------------------------------------------------------
def write_configfile_with_contents(filename, contents, encoding=None):
    encoding = encoding or "UTF-8"
    dirname = os.path.dirname(filename) or "."
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    # PREPARED: with open(filename, "w", encoding=encoding) as config_file:
    with open(filename, "w") as config_file:
        config_file.write(contents)
