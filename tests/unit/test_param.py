# -*- coding: UTF-8 -*-
"""
Unit tests for :class:`click_configfile.Param`.
"""

from __future__ import absolute_import, print_function
from click_configfile import Param
import click.types
import pytest

# TODO: More tests
class TestParam(object):

    def test_ctor__without_type_attribute_has_string_type(self):
        param = Param()
        assert isinstance(param.type, click.types.StringParamType)

    def test_ctor__with_help_attribute(self):
        param = Param(help="Hello")
        assert param.help == "Hello"

    def test_ctor__without_help_attribute(self):
        param = Param()
        assert param.help is None
