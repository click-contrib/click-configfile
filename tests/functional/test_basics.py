# -*- coding: UTF-8 -*-
"""
Test basic functionality
"""

from __future__ import absolute_import, print_function
import os.path
from tests._test_support import write_configfile_with_contents
from click_configfile import Param, SectionSchema, ConfigFileReader, \
    assign_param_names, matches_section
import click
import pytest
import six


# -----------------------------------------------------------------------------
# TEST SUPPORT:
# -----------------------------------------------------------------------------
def posix_normpath(p):
    if not p:
        return p or ""

    assert isinstance(p, six.string_types)
    return p.replace("\\", "/")


# -----------------------------------------------------------------------------
# TEST CANDIDATE 1:
# -----------------------------------------------------------------------------
@assign_param_names
class ConfigSectionSchema1(object):

    @matches_section("hello")
    class Hello(SectionSchema):
        name = Param(type=str)
        number = Param(type=int)

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
# TEST CANDIDATE 2:
# -----------------------------------------------------------------------------
@assign_param_names
class ConfigSectionSchema2(object):

    @matches_section("hello2")
    class Hello(SectionSchema):
        name = Param(type=str)

    @matches_section("hello2.*")
    class HelloMore(SectionSchema):
        numbers = Param(type=int, multiple=True)

class ConfigFileProcessor2(ConfigFileReader):
    config_files = ["hello2.ini", "hello2.cfg"]
    config_section_schemas = [
        ConfigSectionSchema2.Hello,
        ConfigSectionSchema2.HelloMore,
    ]


# -----------------------------------------------------------------------------
# TEST CANDIDATE 3: With config_searchpath
# -----------------------------------------------------------------------------
class ConfigFileProcessor3(ConfigFileReader):
    config_files = ["hello3.ini"]
    config_searchpath = [".", "config/profile"]
    config_section_schemas = [
        ConfigSectionSchema1.Hello,
    ]


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
xfail = pytest.mark.xfail

class TestCandidate1(object):
    def test_without_configfile__uses_defaults_from_cmdline(self, cli_runner):
        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor1.read_config())
        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        def hello(name):
            click.echo("Hello %s" % name)

        assert not os.path.exists("hello.ini")
        result = cli_runner.invoke(hello)
        assert result.output == "Hello __CMDLINE__\n"
        assert result.exit_code == 0

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
        assert result.output == "Hello CMDLINE_VALUE\n"
        assert result.exit_code == 0

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
        assert result.output == "Hello Alice\n"
        assert result.exit_code == 0

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
        assert result.output == "Hello Bob\n"
        assert result.exit_code == 0

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
        assert result.output == "Hello alice\n"
        assert result.exit_code == 0

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
            hello_foo = ctx.default_map["foo"]
            hello_bar = ctx.default_map["bar"]
            click.echo("foo.numbers: %s" % repr(hello_foo["numbers"]))
            click.echo("bar.numbers: %s" % repr(hello_bar["numbers"]))

        assert os.path.exists("hello.ini")
        result = cli_runner_isolated.invoke(hello)
        expected_output = """\
Hello Alice
foo.numbers: [1, 2, 3]
bar.numbers: [1]
"""
        assert result.output == expected_output
        assert result.exit_code == 0


class TestCandidate2(object):

    def test_configfile__use_default_section_to_storage_name_mapping(self,
                                                               cli_runner_isolated):
        assert ConfigFileProcessor2.config_files[0] == "hello2.ini"
        assert not os.path.exists("hello2.cfg")
        CONFIG_FILE_CONTENTS = """
                [hello2]
                name = Alice

                [hello2.foo]
                numbers = 1 2 3

                [hello2.bar]
                numbers = 42
                """
        write_configfile_with_contents("hello2.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello2.ini")

        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor2.read_config())

        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", default="__CMDLINE__")
        @click.pass_context
        def hello2(ctx, name):
            click.echo("Hello2 %s" % name)
            hello2_foo = ctx.default_map["hello2.foo"]
            hello2_bar = ctx.default_map["hello2.bar"]
            click.echo("foo.numbers: %s" % repr(hello2_foo["numbers"]))
            click.echo("bar.numbers: %s" % repr(hello2_bar["numbers"]))

        assert os.path.exists("hello2.ini")
        result = cli_runner_isolated.invoke(hello2)
        expected_output = """\
Hello2 Alice
foo.numbers: [1, 2, 3]
bar.numbers: [42]
"""
        assert result.output == expected_output
        assert result.exit_code == 0


class TestCandidate2B(object):

    def test_configfile__with_unbound_section(self, cli_runner_isolated):
        # -- DEFINITION: unbound section
        #   A config section without associated schema but that should be used.
        class ConfigFileProcessorWithUnboundSection(ConfigFileProcessor2):
            config_sections = ["unbound.section"] + \
                    ConfigFileProcessor2.collect_config_sections_from_schemas()

        assert ConfigFileProcessor2.config_files[0] == "hello2.ini"
        assert not os.path.exists("hello2.cfg")
        CONFIG_FILE_CONTENTS = """
                    [hello2]
                    name = Alice

                    [unbound.section]
                    numbers = 42
                    """
        write_configfile_with_contents("hello2.ini", CONFIG_FILE_CONTENTS)
        assert os.path.exists("hello2.ini")

        with pytest.raises(LookupError) as e:
            # -- POINT: CONTEXT_SETTINGS = dict(default_map=...)
            ConfigFileProcessorWithUnboundSection.read_config()

        expected = "LookupError: No schema found for: section=unbound.section"
        assert expected in str(e)


class TestCandidate3(object):

    def test_config_searchpath__with_many_items(self, cli_runner_isolated):
        assert not os.path.exists("hello3.ini")
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = Alice
            """
        CONFIG_FILE_CONTENTS2 = """
            [hello]
            name = Bob
            number = 2
            """
        config_filename2 = os.path.join("config", "profile", "hello3.ini")
        config_dirname2 = os.path.dirname(config_filename2)
        write_configfile_with_contents("hello3.ini", CONFIG_FILE_CONTENTS1)
        write_configfile_with_contents(config_filename2, CONFIG_FILE_CONTENTS2)
        assert os.path.exists("hello3.ini")
        assert os.path.exists(config_filename2)
        assert posix_normpath(config_dirname2) in ConfigFileProcessor3.config_searchpath

        config = ConfigFileProcessor3.read_config()
        assert config == dict(name="Alice", number=2)
        assert config["name"] == "Alice"    # -- FROM: config_file1 (prefered)
        assert config["number"] == 2        # -- FROM: config_file2


    def test_config_searchpath__merges_sections(self, cli_runner_isolated):
        assert not os.path.exists("hello3.ini")
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = Alice
            """
        CONFIG_FILE_CONTENTS2 = """
            [hello]
            number = 2
            """
        config_filename2 = os.path.join("config", "profile", "hello3.ini")
        config_dirname2 = os.path.dirname(config_filename2)
        write_configfile_with_contents("hello3.ini", CONFIG_FILE_CONTENTS1)
        write_configfile_with_contents(config_filename2, CONFIG_FILE_CONTENTS2)
        assert os.path.exists("hello3.ini")
        assert os.path.exists(config_filename2)
        assert posix_normpath(config_dirname2) in ConfigFileProcessor3.config_searchpath

        config = ConfigFileProcessor3.read_config()
        assert config == dict(name="Alice", number=2)
        assert config["name"] == "Alice"    # -- FROM: config_file1 (prefered)
        assert config["number"] == 2        # -- FROM: config_file2


    def test_config_searchpath__param_from_primary_file_overrides_secondary(self,
            cli_runner_isolated):
        assert not os.path.exists("hello3.ini")
        CONFIG_FILE_CONTENTS1 = """
            [hello]
            name = Alice
            """
        CONFIG_FILE_CONTENTS2 = """
            [hello]
            name = Bob      # Will be overridden.
            """
        config_filename2 = os.path.join("config", "profile", "hello3.ini")
        config_dirname2 = os.path.dirname(config_filename2)
        write_configfile_with_contents("hello3.ini", CONFIG_FILE_CONTENTS1)
        write_configfile_with_contents(config_filename2, CONFIG_FILE_CONTENTS2)
        assert os.path.exists("hello3.ini")
        assert os.path.exists(config_filename2)
        assert posix_normpath(config_dirname2) in ConfigFileProcessor3.config_searchpath

        config = ConfigFileProcessor3.read_config()
        assert config == dict(name="Alice")
        assert config["name"] == "Alice"    # -- FROM: config_file1 (prefered)
