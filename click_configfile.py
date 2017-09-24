# -*- coding: UTF-8 -*-
# (c) 2016 by Jens Engel
# pylint: disable=missing-docstring, too-few-public-methods
"""
This module provides functionality to read configuration files with commands
that already use click_ for command-line processing.

.. _click:  http://click.pocoo.org/
"""

from __future__ import absolute_import, print_function
from fnmatch import fnmatch
import os.path
import inspect
import configparser     # -- USE BACKPORT FOR: Python2
from click.types import convert_type
import six

# -----------------------------------------------------------------------------
# PACKAGE META DATA:
# -----------------------------------------------------------------------------
__version__ = "0.2.3"
__author__ = "Jens Engel"
__license__ = "BSD"


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
    elif not isinstance(section_name, (list, tuple)):
        raise ValueError("%r (expected: string, strings)" % section_name)

    def decorator(cls):
        class_section_names = getattr(cls, "section_names", None)
        if class_section_names is None:
            cls.section_names = list(section_names)
        else:
            # -- BETTER SUPPORT: For multiple decorators
            #   @matches_section("foo")
            #   @matches_section("bar.*")
            #   class Example(SectionSchema):
            #       pass
            #   assert Example.section_names == ["foo", "bar.*"]
            approved = [name for name in section_names
                        if name not in cls.section_names]
            cls.section_names = approved + cls.section_names
        return cls
    return decorator


def assign_param_names(cls=None, param_class=None):
    """Class decorator to assign parameter name to instances of :class:`Param`.

    .. sourcecode::

        @assign_param_names
        class ConfigSectionSchema(object):
            alice = Param(type=str)
            bob   = Param(type=str)

        assert ConfigSectionSchema.alice.name == "alice"
        assert ConfigSectionSchema.bob.name == "bob"

    .. sourcecode::

        # -- NESTED ASSIGN: Covers also nested SectionSchema subclasses.
        @assign_param_names
        class ConfigSectionSchema(object):
            class Foo(SectionSchema):
                alice = Param(type=str)
                bob   = Param(type=str)

        assert ConfigSectionSchema.Foo.alice.name == "alice"
        assert ConfigSectionSchema.Foo.bob.name == "bob"
    """
    if param_class is None:
        param_class = Param

    def decorate_class(cls):
        for name, value in select_params_from_section_schema(cls, param_class,
                                                             deep=True):
            # -- ANNOTATE PARAM: By assigning its name
            if not value.name:
                value.name = name
        return cls

    # -- DECORATOR LOGIC:
    if cls is None:
        # -- CASE: @assign_param_names
        # -- CASE: @assign_param_names(...)
        return decorate_class
    else:
        # -- CASE: @assign_param_names class X: ...
        # -- CASE: assign_param_names(my_class)
        # -- CASE: my_class = assign_param_names(my_class)
        return decorate_class(cls)

# -----------------------------------------------------------------------------
# CONFIG SECTION SCHEMA DESCRIPTION
# -----------------------------------------------------------------------------
class SectionSchema(object):
    """Marker for configuration section schema classes."""
    # -- ONLY IN DERIVED CLASSES:
    # section_names = []  # Section names (or patterns) to apply SectionSchema.

    @classmethod
    def matches_section(cls, section_name, supported_section_names=None):
        """Indicates if this schema can be used for a config section
        by using the section name.

        :param section_name:    Config section name to check.
        :return: True, if this schema can be applied to the config section.
        :return: Fals, if this schema does not match the config section.
        """
        if supported_section_names is None:
            supported_section_names = getattr(cls, "section_names", None)

        # pylint: disable=invalid-name
        for supported_section_name_or_pattern in supported_section_names:
            if fnmatch(section_name, supported_section_name_or_pattern):
                return True
        # -- OTHERWISE:
        return False



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
    """
    # pylint: disable=redefined-builtin

    def __init__(self, name=None, type=None, multiple=None, default=None,
                 help=None):
        self.name = name
        self.type = convert_type(type, default)
        self.multiple = multiple
        self.default = default
        self.help = help

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
def select_params_from_section_schema(section_schema, param_class=Param,
                                      deep=False):
    """Selects the parameters of a config section schema.

    :param section_schema:  Configuration file section schema to use.
    :return: Generator of params
    """
    # pylint: disable=invalid-name
    for name, value in inspect.getmembers(section_schema):
        if name.startswith("__") or value is None:
            continue    # pragma: no cover
        elif inspect.isclass(value) and deep:
            # -- CASE: class => SELF-CALL (recursively).
            # pylint: disable= bad-continuation
            cls = value
            for name, value in select_params_from_section_schema(cls,
                                            param_class=param_class, deep=True):
                yield (name, value)
        elif isinstance(value, param_class):
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
        # print("  %s = %s" % (name, repr(value)))
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
        for config_basename in reversed(config_files):
            config_fname = os.path.join(config_path, config_basename)
            if os.path.isfile(config_fname):
                # MAYBE: yield os.path.normpath(config_fname)
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


# -----------------------------------------------------------------------------
# BOILER-PLATE FOR CONFIG-FILE READER
# -----------------------------------------------------------------------------
class ConfigFileReader(object):
    """Generic configuration file reader.
    Concrete configuration file reader class must extend it and specify the
    concrete details.

    EXAMPLE:

    .. sourcecode::

        # -- FILE: hello_command.py
        from click_configfile import ConfigFileReader, Param, SectionSchema
        from click_configfile import matches_section

        class ConfigSectionSchema(object):

            @matches_section("hello")
            class Hello(SectionSchema):
                name = Param(type=str)

            @matches_section("hello.more.*")
            class HelloMore(SectionSchema):
                numbers = Param(type=int, multiple=True)

        class ConfigFileProcessor(ConfigFileReader):
            config_files = ["hello.ini", "hello.cfg"]
            config_section_schemas = [
                ConfigSectionSchema.Hello,     # PRIMARY SCHEMA
                ConfigSectionSchema.HelloMore,
            ]

            @classmethod
            def get_storage_name_for(cls, section_name):
                if section_name == "hello":
                    return ""   # -- MERGE-INTO-STORAGE
                elif section_name.startswith("hello.more."):
                    # -- EXAMPLE:  hello.more.alice  ->  alice
                    return section_name.replace("hello.more.", "", 1)
                # -- OTHERWISE: Delegate to BaseClass
                return ConfigFileReader.get_storage_name_for(section_name)
                # OR: raise LookupError(section_name)


        # -- COMMANDS:
        CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor.read_config())

        @click.command(context_settings=CONTEXT_SETTINGS)
        @click.option("-n", "--name", type=str)
        @click.pass_context
        def hello(ctx, name):
            pass
    """
    config_files = []               # Config filename variants (basenames).
    config_section_schemas = []     # Config section schema description.
    config_sections = []            # OPTIONAL: Config sections of interest.
    config_searchpath = ["."]       # OPTIONAL: Where to look for config files.

    # -- GENERIC PART:
    # Uses declarative specification from above (config_files, config_sections, ...)
    @classmethod
    def read_config(cls):
        configfile_names = list(
            generate_configfile_names(cls.config_files, cls.config_searchpath))
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(configfile_names)

        if not cls.config_sections:
            # -- AUTO-DISCOVER (once): From cls.config_section_schemas
            cls.config_sections = cls.collect_config_sections_from_schemas()

        storage = {}
        for section_name in select_config_sections(parser.sections(),
                                                   cls.config_sections):
            # print("PROCESS-SECTION: %s" % section_name)
            config_section = parser[section_name]
            cls.process_config_section(config_section, storage)
        return storage

    @classmethod
    def collect_config_sections_from_schemas(cls, config_section_schemas=None):
        # pylint: disable=invalid-name
        """Derive support config section names from config section schemas.
        If no :param:`config_section_schemas` are provided, the schemas from
        this class are used (normally defined in the DerivedClass).

        :param config_section_schemas:  List of config section schema classes.
        :return: List of config section names or name patterns (as string).
        """
        if config_section_schemas is None:
            config_section_schemas = cls.config_section_schemas

        collected = []
        for schema in config_section_schemas:
            collected.extend(schema.section_names)
            # -- MAYBE BETTER:
            # for name in schema.section_names:
            #    if name not in collected:
            #        collected.append(name)
        return collected

    # -- SPECIFIC PART:
    # Specifies which schema to use and where data should be stored.
    @classmethod
    def process_config_section(cls, config_section, storage):
        """Process the config section and store the extracted data in
        the param:`storage` (as outgoing param).
        """
        # -- CONCEPT:
        # if not storage:
        #     # -- INIT DATA: With default parts.
        #     storage.update(dict(_PERSONS={}))

        schema = cls.select_config_schema_for(config_section.name)
        if not schema:
            message = "No schema found for: section=%s"
            raise LookupError(message % config_section.name)

        # -- PARSE AND STORE CONFIG SECTION:
        section_storage = cls.select_storage_for(config_section.name, storage)
        section_data = parse_config_section(config_section, schema)
        section_storage.update(section_data)

    @classmethod
    def select_config_schema_for(cls, section_name):
        """Select the config schema that matches the config section (by name).

        :param section_name:    Config section name (as key).
        :return: Config section schmema to use (subclass of: SectionSchema).
        """
        # pylint: disable=cell-var-from-loop, redefined-outer-name
        for section_schema in cls.config_section_schemas:
            schema_matches = getattr(section_schema, "matches_section", None)
            if schema_matches is None:
                # -- OTHER SCHEMA CLASS: Reuse SectionSchema functionality.
                schema_matches = lambda name: SectionSchema.matches_section(
                    name, section_schema.section_names)

            if schema_matches(section_name):
                return section_schema
        return None

    @classmethod
    def get_storage_name_for(cls, section_name):
        """Selects where to store the retrieved data from the config section.

        :param section_name:    Config section name to process (as string).
        :return: EMPTY-STRING or None, indicates MERGE-WITH-DEFAULTS.
        :return: NON-EMPTY-STRING, for key in default_map to use.
        """
        if cls.config_sections and cls.config_sections[0] == section_name:
            # -- PRIMARY-SECTION: Merge into storage (defaults_map).
            return ""
        else:
            return section_name
        # -- MAYBE BETTER:
        # raise LookupError("Unknown section: %s" % section_name)

    @classmethod
    def select_storage_for(cls, section_name, storage):
        """Selects the data storage for a config section within the
        :param:`storage`. The primary config section is normally merged into
        the :param:`storage`.

        :param section_name:    Config section (name) to process.
        :param storage:         Data storage to use.
        :return: :param:`storage` or a part of it (as section storage).
        """
        section_storage = storage
        storage_name = cls.get_storage_name_for(section_name)
        if storage_name:
            section_storage = storage.get(storage_name, None)
            if section_storage is None:
                section_storage = storage[storage_name] = dict()
        return section_storage
