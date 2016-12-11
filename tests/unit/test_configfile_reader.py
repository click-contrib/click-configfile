# -*- coding: UTF-8 -*-
"""
Unit tests for :class:`click_configfile.ConfigFileReader`.
"""

from __future__ import absolute_import, print_function
import os.path
from click_configfile import Param, SectionSchema, ConfigFileReader
from click_configfile import matches_section
from tests._test_support import write_configfile_with_contents
import pytest

# -----------------------------------------------------------------------------
# TEST SUPPORT
# -----------------------------------------------------------------------------
# def write_configfile_with_contents(filename, contents):
#     dirname = os.path.dirname(filename) or "."
#     if not os.path.isdir(dirname):
#         os.makedirs(dirname)
#
#     with open(filename, "w") as config_file:
#         config_file.write(contents)


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
class TestConfigFileReader(object):

    # -- TESTS FOR: ConfigFileReader.select_config_schema_for()
    def test_select_config_schema_for__with_schema_class(self):
        @matches_section("foo")
        class ExampleSchema(SectionSchema):
            number = Param(type=int)

        class ConfigFileProcessor(ConfigFileReader):
            config_section_schemas = [ExampleSchema]

        schema = ConfigFileProcessor.select_config_schema_for("foo")
        assert schema is ExampleSchema

    def test_select_config_schema_for__with_other_schema_class(self):
        @matches_section("foo")
        class ExampleSchema(object):
            number = Param(type=int)

        class ConfigFileProcessor(ConfigFileReader):
            config_section_schemas = [ExampleSchema]

        schema = ConfigFileProcessor.select_config_schema_for("foo")
        assert schema is ExampleSchema

    def test_select_config_schema_for__with_unbound_section(self):
        # -- MEANS: A config section that does not match any schema.
        @matches_section("foo")
        class ExampleSchema(object):
            number = Param(type=int)

        class ConfigFileProcessor(ConfigFileReader):
            config_section_schemas = [ExampleSchema]

        schema = ConfigFileProcessor.select_config_schema_for("unbound.section")
        assert schema is None


    # -- TESTS FOR: ConfigFileReader.collect_config_sections_from_schemas()
    def test_collect_config_sections_from_schemas__without_arg(self):
        # -- SETUP:
        @matches_section("foo")
        class ExampleSchema1(SectionSchema):
            number = Param(type=int)

        @matches_section("foo.more.*")
        class ExampleSchema2(SectionSchema):
            name = Param(type=str)

        class ConfigFileProcessor(ConfigFileReader):
            config_section_schemas = [ExampleSchema1, ExampleSchema2]

        # -- PERFORM TEST:
        sections = ConfigFileProcessor.collect_config_sections_from_schemas()
        assert sections == ["foo", "foo.more.*"]


    def test_collect_config_sections_from_schemas__with_arg(self):
        # -- SETUP:
        @matches_section("foo")
        class ExampleSchema1(SectionSchema):
            number = Param(type=int)

        @matches_section("bar.*")
        class ExampleSchema2(SectionSchema):
            name = Param(type=str)

        config_section_schemas = [ExampleSchema1, ExampleSchema2]
        class ConfigFileProcessor(ConfigFileReader):
            pass

        # -- PERFORM TEST:
        sections = ConfigFileProcessor.collect_config_sections_from_schemas(
                        config_section_schemas)
        assert sections == ["foo", "bar.*"]

    # -- TESTS FOR: ConfigFileReader.select_storage_for(section_name, ...)
    def test_select_storage_for__when_section_storage_is_created(self):
        storage = {}
        store = ConfigFileReader.select_storage_for("new.section", storage)
        assert "new.section" in storage
        assert store == dict()
        assert storage["new.section"] == store

        # -- USE SECTION STORE:
        store.update(_stored=True)
        assert storage["new.section"] == store

    def test_select_storage_for__when_section_storage_exists(self):
        initial_section_store = dict(foo=True)
        storage = {
            "existing.section": initial_section_store,
            "bar": False,
        }
        store = ConfigFileReader.select_storage_for("existing.section", storage)
        assert "existing.section" in storage
        assert storage["existing.section"] == store
        assert store == initial_section_store
        assert store == dict(foo=True)

        # -- USE SECTION STORE:
        store.update(_stored=True)
        assert storage["existing.section"] == store

    def test_select_storage_for__when_root_store_is_used(self):
        # -- SETUP:
        @matches_section("hello")
        class ExampleSchema(SectionSchema):
            number = Param(type=int)

        class ConfigFileProcessor(ConfigFileReader):
            config_sections = ["hello"]     # PRIMARY SECTION: Uses root store.
            config_section_schemas = [ExampleSchema]

        # -- PERFORM TEST:
        storage = dict(_root=True)
        store = ConfigFileProcessor.select_storage_for("hello", storage)
        assert store is storage
        assert "_root" in store

        # -- USE SECTION STORE:
        store.update(number=20)
        assert storage == store
