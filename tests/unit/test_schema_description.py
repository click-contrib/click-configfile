# -*- coding: UTF-8 -*-
"""
Unit tests for config section schema description.
"""

from __future__ import absolute_import, print_function
from click_configfile import Param, SectionSchema
from click_configfile import assign_param_names, matches_section
import pytest


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
class TestDecorators(object):

    # -- TESTS RELATED TO: @assign_param_names decorator
    def test_assign_param_names__with_schema_class(self):
        @assign_param_names
        class ExampleSchema(SectionSchema):
            some_non_param = 123
            person = Param(type=str)
            number = Param(type=int)
            verbose = Param(type=bool)
            persons = Param(type=str, multiple=True)

        # -- ENSURE:
        assert ExampleSchema.person.name == "person"
        assert ExampleSchema.number.name == "number"
        assert ExampleSchema.verbose.name == "verbose"
        assert ExampleSchema.persons.name == "persons"

    def test_assign_param_names__with_other_class(self):
        @assign_param_names
        class ExampleSchema(object):
            person = Param(type=str)
            number = Param(type=int)

        # -- ENSURE:
        assert ExampleSchema.person.name == "person"
        assert ExampleSchema.number.name == "number"

    def test_assign_param_names__with_nested_schema_class(self):
        @assign_param_names
        class ConfigSectionSchema(object):
            class Example(SectionSchema):
                person = Param(type=str)
                number = Param(type=int)

        # -- ENSURE:
        assert ConfigSectionSchema.Example.person.name == "person"
        assert ConfigSectionSchema.Example.number.name == "number"

    def test_assign_param_names__with_deeper_nested_schema_class(self):
        @assign_param_names
        class ConfigSectionSchema(object):
            class Level(object):
                class Example(SectionSchema):
                    person = Param(type=str)
                    number = Param(type=int)

        # -- ENSURE:
        assert ConfigSectionSchema.Level.Example.person.name == "person"
        assert ConfigSectionSchema.Level.Example.number.name == "number"

    def test_assign_param_names__with_derived_param_class_in_schema(self):
        class DerivedParam(Param):
            pass

        @assign_param_names
        class ExampleSchema(object):
            person = DerivedParam(type=str)
            number = DerivedParam(type=int)

        # -- ENSURE:
        assert ExampleSchema.person.name == "person"
        assert ExampleSchema.number.name == "number"

    def test_assign_param_names__with_own_param_class_as_marker(self):
        class MyParam(Param):
            pass

        @assign_param_names(param_class=MyParam)
        class ExampleSchema(object):
            person = Param(type=str)
            number = MyParam(type=int)

        # -- ENSURE:
        assert ExampleSchema.person.name is None
        assert ExampleSchema.number.name == "number"


    def test_assign_param_names__skips_non_param_objects(self):
        @assign_param_names
        class ExampleSchema(SectionSchema):
            some_non_param = 123
            param_class_alias = Param

        # -- ENSURE:
        assert not hasattr(ExampleSchema.some_non_param, "name")
        assert not hasattr(ExampleSchema.param_class_alias, "name")

    def test_assign_param_names__skips_params_with_assigned_names(self):
        @assign_param_names
        class ExampleSchema(SectionSchema):
            person = Param("xxx", type=str)
            number = Param(name="PHI", type=float)

        # -- ENSURE:
        assert ExampleSchema.person.name == "xxx"
        assert ExampleSchema.number.name == "PHI"


    # -- TESTS RELATED TO: @matches_section decorator
    @pytest.mark.parametrize("section_name", [
        "hello", "hello.*", "*.hello"
    ])
    def test_matches_section__with_arg(self, section_name):
        @matches_section(section_name)
        class Hello(SectionSchema):
            pass

        assert Hello.section_names == [section_name]

    @pytest.mark.parametrize("section_names", [
        ["hello", "hello.*"]
    ])
    def test_matches_section__with_multiple_args(self, section_names):
        @matches_section(section_names)
        class Hello(SectionSchema):
            pass

        assert isinstance(section_names, (list, tuple))
        assert Hello.section_names == section_names

    def test_matches_section__with_several_decorators(self):
        @matches_section("foo")
        @matches_section("bar.*")
        class Hello(SectionSchema):
            pass

        assert Hello.section_names == ["foo", "bar.*"]

    def test_matches_section__with_other_class(self):
        @matches_section("hello")
        class Hello(object):
            pass

        assert Hello.section_names == ["hello"]

    def test_matches_section__with_class_that_has_section_names(self):
        @matches_section("hello")
        class Hello(SectionSchema):
            section_names = ["foo"]

        assert Hello.section_names == ["hello", "foo"]

    @pytest.mark.parametrize("bad_section_name", [None, 123, False, 1.23])
    def test_matches_section__with_bad_arg(self, bad_section_name):
        with pytest.raises(ValueError) as e:
            @matches_section(bad_section_name)
            class Hello(SectionSchema):
                pass

        expected = "ValueError: %r (expected: string, strings)" % bad_section_name
        assert expected in str(e)
