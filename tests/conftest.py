# -*- coding: UTF-8 -*-
"""
Pytest configuration file.
"""
from click.testing import CliRunner
import pytest

@pytest.fixture(scope="function")
def cli_runner(request):
    """click_ CLI runner to execute click_ commands.

    .. _click: https://click.pocoo.org/
    """
    return CliRunner()

@pytest.fixture(scope="function")
def cli_runner_isolated(request):
    """click_ CLI runner that provides an isolated filesystem.

    .. _click: https://click.pocoo.org/
    """
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem():
        yield cli_runner

@pytest.fixture(scope="function")
def isolated_filesystem(request):
    """click_ CLI runner that provides an isolated filesystem.

    .. _click: https://click.pocoo.org/
    """
    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem() as _isolated_filesystem:
        yield _isolated_filesystem
