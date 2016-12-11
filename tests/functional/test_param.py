# -*- coding: UTF-8 -*-
"""
Test parameter related functionality.
"""

from __future__ import absolute_import, print_function
import os.path
from tests._test_support import write_configfile_with_contents
from click_configfile import Param, SectionSchema, ConfigFileReader, \
    assign_param_names, matches_section
import click
import pytest


# -----------------------------------------------------------------------------
# TEST CANDIDATE 1:
# -----------------------------------------------------------------------------
@assign_param_names
class ConfigSectionSchema1(object):

    @matches_section("hello")
    class Hello(SectionSchema):
        name    = Param(type=str)
        number  = Param(type=int, default=42)


class ConfigFileProcessor1(ConfigFileReader):
    config_files = ["hello.ini"]
    config_section_schemas = [
        ConfigSectionSchema1.Hello,
    ]


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
xfail = pytest.mark.xfail

class TestCandidate1(object):

    def test_param_with_default__uses_param_default_when_missing(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        CONFIG_FILE_CONTENTS = """
            [hello]
            name = Alice
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello.ini")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", type=str, default="__CMDLINE__")
        @click.option("--number", default=123)
        def hello_with_param_default(name, number):
            click.echo("param: number= %s" % number)

        result = cli_runner_isolated.invoke(hello_with_param_default)
        assert result.output == "param: number= 42\n"
        assert result.exit_code == 0

    def test_param_with_default__uses_cmdline_when_provided(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        CONFIG_FILE_CONTENTS = """
            [hello]
            name = Alice
            number = 43
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello.ini")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", type=str, default="__CMDLINE__")
        @click.option("--number", default=123)
        def hello_with_param_default2(name, number):
            click.echo("param: number= %s" % number)

        result = cli_runner_isolated.invoke(hello_with_param_default2,
                                            ["--number", "234"])
        assert result.output == "param: number= 234\n"
        assert result.exit_code == 0

    def test_param_without_default__uses_cmdline_default_when_missing(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        CONFIG_FILE_CONTENTS = """
            [hello]
            number = 1234
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello.ini")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", type=str, default="__CMDLINE__")
        def hello_with_config(name):
            click.echo("param: name= %s" % name)

        result = cli_runner_isolated.invoke(hello_with_config)
        assert result.output == "param: name= __CMDLINE__\n"
        assert result.exit_code == 0

