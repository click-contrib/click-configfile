# -*- coding: UTF-8 -*-
"""
Pytest configuration file.
"""
from click.testing import CliRunner
import pytest

@pytest.fixture(scope="function")
def runner(request):
    return CliRunner()

@pytest.fixture(scope="function")
def isolated_runner(request):
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
