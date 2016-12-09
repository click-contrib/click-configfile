# -*- coding: UTF-8 -*-
"""
This module provides some helpers to read configuration files with commands
that already use click (for command-line processing).

"""

from __future__ import absolute_import, print_function
from fnmatch import fnmatch
import os.path
import inspect
from click.types import convert_type
import six


# -----------------------------------------------------------------------------
# DECORATORS
# -----------------------------------------------------------------------------
def matches_section(section_name):
    """Decorator for SectionSchema classes to define the mapping between
    a config section schema class and one or more config sections with
    matching name(s).

    .. sourcecode::

        @matches_section("foo")
        class FooSchema(SectionSchema):
            pass

        @matches_section(["bar", "baz.*"])
        class BarAndBazSchema(SectionSchema):
            pass

    .. sourcecode:: ini

        # -- FILE: *.ini
        [foo]       # USE: FooSchema
        ...

        [bar]       # USE: BarAndBazSchema
        ...

        [baz.alice] # USE: BarAndBazSchema
        ...
    """
    section_names = section_name
    if isinstance(section_name, six.string_types):
        section_names = [section_name]

    def decorator(cls):
        # pylint: disable=protected-access
        _section_names = getattr(cls, "_section_names", None)
        if _section_names is None:
            cls._section_names = list(section_names)
        else:
            cls._section_names.extend(section_names)
        return cls
    return decorator


# -----------------------------------------------------------------------------
# CONFIG SECTION SCHEMA DESCRIPTION
# -----------------------------------------------------------------------------
class SectionSchema(object):
    """Marker for configuration section schema classes (syntactic sugar)."""
    pass


class Param(object):
    """Simple Parameter class used for description config file schema params.
    Simple replacement for :class:`click.Parameter` or its variants.
    Click types are supported.

    .. sourcecode::

            class FooSchema(SectionSchema):
                name    = Param(type=str)
                flag    = Param(type=bool, default=True)
                numbers = Param(type=int, multiple=True)
                filenames = Param(type=click.Path(), multiple=True)

    .. sourcecode:: ini

        # -- FILE: foo.ini
        [foo]
        flag = yes      # -- SUPPORTS: true, false, yes, no (case-insensitive)
        name = Alice and Bob
        numbers = 1 4 9 16 25
        filenames = foo/xxx.txt
            bar/baz/zzz.txt

    .. todo:: NICE TO HAVE: Auto-discover name from stack.
    """
    # pylint: disable=redefined-builtin
    def __init__(self, name=None, type=None, multiple=None, default=None):
        self.name = name
        self.type = convert_type(type, default)
        self.multiple = multiple
        self.default = default

    def parse(self, text):
        if self.multiple:
            parts = text.strip().split()
            values = [self.type.convert(value, self, ctx=None)
                      for value in parts]
            return values
        else:
            return self.type.convert(text, self, ctx=None)


# -----------------------------------------------------------------------------
# PARSING CONFIG SECTIONS WITH SCHEMA DESCRIPTION
# -----------------------------------------------------------------------------
def select_params_from_section_schema(section_schema):
    """Selects the parameters of a config section schema.

    :param section_schema:  Configuration file section schema to use.
    :return: Generator of params
    """
    # pylint: disable=invalid-name
    for name, value in inspect.getmembers(section_schema):
        if name.startswith("_"):
            continue
        elif isinstance(value, Param):
            yield (name, value)


def parse_config_section(config_section, section_schema):
    """Parse a config file section (INI file) by using its schema/description.

    .. sourcecode::

        import configparser     # -- NOTE: Use backport for Python2
        import click
        from click_configfile import SectionSchema, Param, parse_config_section

        class ConfigSectionSchema(object):
            class Foo(SectionSchema):
                name    = Param(type=str)
                flag    = Param(type=bool)
                numbers = Param(type=int, multiple=True)
                filenames = Param(type=click.Path(), multiple=True)

        parser = configparser.ConfigParser()
        parser.read(["foo.ini"])
        config_section = parser["foo"]
        data = parse_config_section(config_section, ConfigSectionSchema.Foo)
        # -- FAILS WITH: click.BadParameter if conversion errors occur.

    .. sourcecode:: ini

        # -- FILE: foo.ini
        [foo]
        name = Alice
        flag = yes      # true, false, yes, no (case-insensitive)
        numbers = 1 4 9 16 25
        filenames = foo/xxx.txt
            bar/baz/zzz.txt

    :param config_section:  Config section to parse
    :param section_schema:  Schema/description of config section (w/ Param).
    :return: Retrieved data, values converted to described types.
    :raises: click.BadParameter, if conversion error occurs.
    """
    # print("config_section: %s" % config_section.name)
    storage = {}
    for name, param in select_params_from_section_schema(section_schema):
        value = config_section.get(name, None)
        if value is None:
            if param.default is None:
                continue
            value = param.default
        else:
            value = param.parse(value)
        # -- DIAGNOSTICS:
        print("  %s = %s" % (name, repr(value)))
        storage[name] = value
    return storage


# -----------------------------------------------------------------------------
# SUPPORT: READ CONFIGFILE
# -----------------------------------------------------------------------------
def generate_configfile_names(config_files, config_searchpath=None):
    """Generates all configuration file name combinations to read.

    .. sourcecode::

        # -- ALGORITHM:
        #    First basenames/directories are prefered and override other files.
        for config_path in reversed(config_searchpath):
            for config_basename in reversed(config_files):
                config_fname = os.path.join(config_path, config_basename)
                if os.path.isfile(config_fname):
                    yield config_fname

    :param config_files:        List of config file basenames.
    :param config_searchpath:   List of directories to look for config files.
    :return: List of available configuration file names (as generator)
    """
    if config_searchpath is None:
        config_searchpath = ["."]

    for config_path in reversed(config_searchpath):
        if not os.path.isdir(config_path):
            continue

        for config_basename in reversed(config_files):
            config_fname = os.path.join(config_path, config_basename)
            if os.path.isfile(config_fname):
                yield config_fname


def select_config_sections(configfile_sections, desired_section_patterns):
    """Select a subset of the sections in a configuration file by using
    a list of section names of list of section name patters
    (supporting :mod:`fnmatch` wildcards).

    :param configfile_sections: List of config section names (as strings).
    :param desired_section_patterns:
    :return: List of selected section names or empty list (as generator).
    """
    for section_name in configfile_sections:
        for desired_section_pattern in desired_section_patterns:
            if fnmatch(section_name, desired_section_pattern):
                yield section_name

