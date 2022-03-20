Configuration File Support for Click Commands
===============================================================================

.. image:: https://github.com/click-contrib/click-configfile/actions/workflows/test.yml/badge.svg
    :target: https://github.com/click-contrib/click-configfile/actions/workflows/test.yml
    :alt: CI Build Status

.. image:: https://img.shields.io/pypi/v/click-configfile.svg
    :target: https://pypi.org/project/click-configfile
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/click-configfile.svg
    :target: https://pypi.org/project/click-configfile
    :alt: Downloads

.. image:: https://img.shields.io/pypi/l/click-configfile.svg
    :target: https://pypi.org/project/click-configfile/
    :alt: License


click_ is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.

This package extends the click_ functionality by adding support for commands
that use configuration files.

.. _click: https://click.pocoo.org/


EXAMPLE:

.. code-block:: python

    # -- FILE: example_command_with_configfile.py (PART 1)
    # BASIC SOLUTION FOR: Command that uses one or more configuration files.
    import click

    CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor.read_config())

    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("-n", "--number", "numbers", type=int, multiple=True)
    @click.pass_context
    def command_with_config(ctx, numbers):
        """Example for a command that uses an configuration file"""
        pass
        ...

    if __name__ == "__main__":
        command_with_config()

The command implementation reads the configuraion file(s) by using the
``ConfigFileProcessor.read_config()`` method and stores it in the
``default_map`` of the ``context_settings``.

That is only the first part of the problem. We have now a solution that allows
us to read configuration files (and override the command options defaults)
before the command-line parsing begins.

In addition, there should be a simple way to specify the configuration schema
in the configuration file in a similar way like the command-line options.
An example how this functionality may look like, is shown in the following
code snippet:

.. code-block:: python

    # -- FILE: example_command_with_configfile.py (PART 2)
    # Description of sections in a confguration file: *.ini
    from click_configfile import matches_section, Param, SectionSchema

    class ConfigSectionSchema(object):
        """Describes all config sections of this configuration file."""

        @matches_section("foo")
        class Foo(SectionSchema):
            name    = Param(type=str)
            flag    = Param(type=bool, default=True)
            numbers = Param(type=int, multiple=True)
            filenames = Param(type=click.Path(), multiple=True)

        @matches_section("person.*")   # Matches multiple sections
        class Person(SectionSchema):
            name      = Param(type=str)
            birthyear = Param(type=click.IntRange(1990, 2100))



The example shows that the ``Param`` class supports similar arguments like a
``click.Option``. You can specify:

* a ``type`` (converter), like in click_ options
* a ``multiple`` flag that is used for sequences of a type
* an optional ``default`` value (if needed or used as type hint)

An example for a valid configuration file with this schema is:

.. code-block:: INI

    # -- FILE: foo.ini
    [foo]
    flag = yes      # -- SUPPORTS: true, false, yes, no (case-insensitive)
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


The following code snippet shows the remaing core implementation of reading
the configuration file (and parsing the configuration file data):

.. code-block:: python

    # -- FILE: example_command_with_configfile.py (PART 3)
    import configparser     # HINT: Use backport for Python2
    from click_configparser import generate_configfile_names, \
        select_config_sections, parse_config_section

    class ConfigFileProcessor(object):
        config_files = ["foo.ini", "foo.cfg"]   # Config filename variants.
        config_sections = ["foo", "person.*"]   # Sections of interest.
        config_section_schemas = [
            ConfigSectionSchema.Foo,
            ConfigSectionSchema.Person,
        ]

        # -- GENERIC PART:
        # Uses declarative specification from above (config_files, config_sections, ...)
        @classmethod
        def read_config(cls):
            configfile_names = list(generate_configfile_names(cls.config_files))
            print("READ-CONFIG: %s" % repr(configfile_names))
            parser = configparser.ConfigParser()
            parser.optionxform = str
            parser.read(configfile_names)

            storage = {}
            for section_name in select_config_sections(parser.sections(),
                                                       cls.config_sections):
                config_section = parser[section_name]
                cls.process_config_section(config_section, storage)
            return storage

        # -- SPECIFIC PART:
        # Specifies which schema to use and where data should be stored.
        @classmethod
        def process_config_section(cls, config_section, storage):
            """Process the config section and store the extracted data in
            the param:`storage` (as outgoing param).
            """
            if not storage:
                # -- INIT DATA: With default parts.
                storage.update(dict(_PERSONS={}))

            if config_section.name == "foo":
                schema = ConfigSectionSchema.Foo
                section_data = parse_config_section(config_section, schema)
                storage.update(section_data)
            elif section_name.startswith("persons."):
                person_name = section_name.replace("person.", "", 1)
                schema = ConfigSectionSchema.Person
                section_data = parse_config_section(config_section, schema)
                storage["_PERSONS"][person_name] = section_data
            # -- HINT: Ignore unknown section for extensibility reasons.


The source code snippet above already contains a large number of generic
functionality. Most of it can be avoided for processing a specific
configuration file by using the ``ConfigFileReader`` class.
The resulting source code is:

.. code-block:: python

    # MARKER-EXAMPLE:
    # -- FILE: example_command_with_configfile.py (ALL PARTS: simplified)
    from click_configfile import ConfigFileReader, Param, SectionSchema
    from click_configfile import matches_section
    import click

    class ConfigSectionSchema(object):
        """Describes all config sections of this configuration file."""

        @matches_section("foo")
        class Foo(SectionSchema):
            name    = Param(type=str)
            flag    = Param(type=bool, default=True)
            numbers = Param(type=int, multiple=True)
            filenames = Param(type=click.Path(), multiple=True)

        @matches_section("person.*")   # Matches multiple sections
        class Person(SectionSchema):
            name      = Param(type=str)
            birthyear = Param(type=click.IntRange(1990, 2100))


    class ConfigFileProcessor(ConfigFileReader):
        config_files = ["foo.ini", "foo.cfg"]
        config_section_schemas = [
            ConfigSectionSchema.Foo,     # PRIMARY SCHEMA
            ConfigSectionSchema.Person,
        ]

        # -- SIMPLIFIED STORAGE-SCHEMA:
        #   section:person.*        -> storage:person.*
        #   section:person.alice    -> storage:person.alice
        #   section:person.bob      -> storage:person.bob

        # -- ALTERNATIVES: Override ConfigFileReader methods:
        #  * process_config_section(config_section, storage)
        #  * get_storage_name_for(section_name)
        #  * get_storage_for(section_name, storage)


    # -- COMMAND:
    CONTEXT_SETTINGS = dict(default_map=ConfigFileProcessor.read_config())

    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("-n", "--number", "numbers", type=int, multiple=True)
    @click.pass_context
    def command_with_config(ctx, numbers):
        # -- ACCESS ADDITIONAL DATA FROM CONFIG FILES: Using ctx.default_map
        for person_data_key in ctx.default_map.keys():
            if not person_data_key.startswith("person."):
                continue
            person_data = ctx.default_map[person_data_key]
            process_person_data(person_data)    # as dict.
