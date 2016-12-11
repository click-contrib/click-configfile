# -*- coding: UTF-8 -*-
"""
Unit tests for :class:`click_configfile.ConfigFileReader`.
"""

from __future__ import absolute_import, print_function
import os.path
from tests._test_support import write_configfile_with_contents
from click_configfile import generate_configfile_names
import pytest


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
class TestFunction(object):

    # -- TESTS FOR: generate_configfile_names()
    def test_generate_configfile_names__without_config_files(self, isolated_filesystem):
        config_files = list(generate_configfile_names([]))
        assert config_files == []

    def test_generate_configfile_names__provides_reversed_order(self, isolated_filesystem):
        # -- SETUP:
        EMPTY_CONTENTS = "# -- EMPTY\n"
        write_configfile_with_contents("hello.ini", EMPTY_CONTENTS)
        write_configfile_with_contents("hello.cfg", EMPTY_CONTENTS)
        assert os.path.exists("hello.ini")
        assert os.path.exists("hello.cfg")

        # -- PERFROM TEST:
        given_config_files = ["hello.ini", "hello.cfg"]
        actual_config_files = list(generate_configfile_names(given_config_files))
        expected_config_files = [
            os.path.join(".", "hello.cfg"),
            os.path.join(".", "hello.ini"),
        ]
        expected_config_files2 = [os.path.normpath(p)
                                  for p in expected_config_files]
        assert actual_config_files == expected_config_files
        assert list(reversed(given_config_files)) == expected_config_files2

    def test_generate_configfile_names__provides_existing_variants_with_searchpath(self, isolated_filesystem):
        # -- SETUP:
        EMPTY_CONTENTS = "# -- EMPTY\n"
        write_configfile_with_contents("hello.ini", EMPTY_CONTENTS)
        write_configfile_with_contents("more/hello.ini", EMPTY_CONTENTS)
        write_configfile_with_contents("more/hello.cfg", EMPTY_CONTENTS)
        assert os.path.exists("hello.ini")
        assert os.path.exists("more/hello.ini")
        assert os.path.exists("more/hello.cfg")

        # -- PERFROM TEST:
        given_config_files = ["hello.ini", "hello.cfg"]
        config_searchpath = [".", "more"]
        actual_config_files = list(generate_configfile_names(given_config_files,
                                                             config_searchpath))
        expected_config_files = [
            os.path.join("more", "hello.cfg"),
            os.path.join("more", "hello.ini"),
            os.path.join(".", "hello.ini"),
        ]
        assert actual_config_files == expected_config_files

    def test_generate_configfile_names__without_searchpath_uses_curdir(self, isolated_filesystem):
        # -- SETUP:
        EMPTY_CONTENTS = "# -- EMPTY\n"
        write_configfile_with_contents("hello.ini", EMPTY_CONTENTS)
        write_configfile_with_contents("hello.cfg", EMPTY_CONTENTS)
        assert os.path.exists("hello.ini")
        assert os.path.exists("hello.cfg")

        # -- PERFROM TEST:
        given_config_files = ["hello.ini", "hello.cfg"]
        actual_config_files = list(generate_configfile_names(given_config_files))
        expected_config_files = [
            os.path.join(".", "hello.cfg"),
            os.path.join(".", "hello.ini"),
        ]
        assert actual_config_files == expected_config_files

    def test_generate_configfile_names__missing_variants_are_removed(self, isolated_filesystem):
        # -- PRECONDITIONS:
        assert not os.path.exists("hello.ini")
        assert not os.path.exists("hello.cfg")

        # -- PERFROM TEST:
        given_config_files = ["hello.ini", "hello.cfg"]
        actual_config_files = list(generate_configfile_names(given_config_files))
        assert actual_config_files == []

    def test_generate_configfile_names__when_searchpath_part_isfile(self, isolated_filesystem):
        # -- SETUP:
        EMPTY_CONTENTS = "# -- EMPTY\n"
        write_configfile_with_contents("hello.ini", EMPTY_CONTENTS)
        write_configfile_with_contents("BAD_PART", EMPTY_CONTENTS)
        assert os.path.exists("hello.ini")
        assert os.path.exists("BAD_PART")

        # -- PERFROM TEST:
        given_config_files = ["hello.ini", "hello.cfg"]
        config_searchpath = [".", "BAD_PART"]
        actual_config_files = list(generate_configfile_names(given_config_files,
                                                             config_searchpath))
        expected_config_files = [
            os.path.join(".", "hello.ini"),
        ]
        assert actual_config_files == expected_config_files
