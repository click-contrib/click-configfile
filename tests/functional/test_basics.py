# -*- coding: UTF-8 -*-
"""
Test basic functionality
"""

from __future__ import absolute_import, print_function
import os.path
from click_configfile import Param, SectionSchema, ConfigFileReader, \
    assign_param_names, matches_section
import click
import click.core
from click.testing import CliRunner
import pytest

# -----------------------------------------------------------------------------
# TEST SUPPORT
# -----------------------------------------------------------------------------
def write_configfile_with_contents(filename, contents):
    with open(filename, "w") as config_file:
        config_file.write(contents)


# -----------------------------------------------------------------------------
# TEST CANDIDATE 1:
# -----------------------------------------------------------------------------
@assign_param_names
class ConfigSectionSchema1(object):

    @matches_section("hello")
    class Hello(SectionSchema):
        name = Param(type=str)

    @matches_section("hello.more.*")
    class HelloMore(SectionSchema):
        numbers = Param(type=int, multiple=True)


class ConfigFileProcessor1(ConfigFileReader):
    config_files = ["hello.ini", "hello.cfg"]
    config_section_schemas = [
        ConfigSectionSchema1.Hello,
        ConfigSectionSchema1.HelloMore,
    ]

    @classmethod
    def get_storage_name_for(cls, section_name):
        if section_name == "hello":
            return ""
        elif section_name.startswith("hello.more."):
            # -- EXAMPLE:  hello.more.alice  ->  alice
            storage_name = section_name.replace("hello.more.", "", 1)
            return storage_name
        # -- OTHERWISE:
        raise LookupError(section_name)


# -----------------------------------------------------------------------------
# TEST FIXTURES
# -----------------------------------------------------------------------------
# @pytest.fixture
# def runner2():
#     return CliRunner()
#
# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
xfail = pytest.mark.xfail

class TestBasics(object):
    def test_without_configfile__uses_defaults_from_cmdline(self, cli_runner):
        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        assert not os.path.exists("hello.ini")
        result = cli_runner.invoke(hello)
        assert result.exit_code == 0
        assert result.output == "Hello __CMDLINE__\n"

    def test_with_cmdline_and_configfile__prefers_cmdline(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = Alice
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS1)
        assert os.path.exists("hello.ini")
        assert not os.path.exists("hello.cfg")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        result = cli_runner_isolated.invoke(hello, ["--name", "CMDLINE_VALUE"])
        assert result.exit_code == 0
        assert result.output == "Hello CMDLINE_VALUE\n"

    def test_with_configfile1__preferred_over_cmdline_defaults(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = Alice
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS1)
        assert os.path.exists("hello.ini")
        assert not os.path.exists("hello.cfg")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        assert os.path.exists("hello.ini")
        result = cli_runner_isolated.invoke(hello)
        assert result.exit_code == 0
        assert result.output == "Hello Alice\n"

    def test_with_configfile2__usable_as_alternative(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[1] == "hello.cfg"
        CONFIG_FILE_CONTENTS2 = """
            [hello]
            name = Bob
            """
        write_configfile_with_contents("hello.cfg", CONFIG_FILE_CONTENTS2)
        assert not os.path.exists("hello.ini")
        assert os.path.exists("hello.cfg")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        result = cli_runner_isolated.invoke(hello)
        assert result.exit_code == 0
        assert result.output == "Hello Bob\n"

    def test_with_configfile12__prefers_configfile1(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files == ["hello.ini", "hello.cfg"]
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = alice
            """
        CONFIG_FILE_CONTENTS2 = """
            [hello]
            name = bob
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS1)
        write_configfile_with_contents("hello.cfg", CONFIG_FILE_CONTENTS2)
        assert os.path.exists("hello.ini")
        assert os.path.exists("hello.cfg")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        result = cli_runner_isolated.invoke(hello)
        assert result.exit_code == 0
        assert result.output == "Hello alice\n"

    def test_configfile__can_pass_additional_params_in_context(self, cli_runner_isolated):
        assert ConfigFileProcessor1.config_files[0] == "hello.ini"
        assert not os.path.exists("hello.cfg")
        CONFIG_FILE_CONTENTS = """
            [hello]
            name = Alice

            [hello.more.foo]
            numbers = 1 2 3

            [hello.more.bar]
            numbers = 1
            """
        write_configfile_with_contents("hello.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello.ini")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        @click.pass_context
        def hello(ctx, name):
            click.echo("Hello %s" % name)
            click.echo("foo.numbers: %s" % repr(ctx.default_map["foo"]["numbers"]))
            click.echo("bar.numbers: %s" % repr(ctx.default_map["bar"]["numbers"]))

        assert os.path.exists("hello.ini")
        result = cli_runner_isolated.invoke(hello)
        expected_output = """\
Hello Alice
foo.numbers: [1, 2, 3]
bar.numbers: [1]
"""
        assert result.exit_code == 0
        assert result.output == expected_output
