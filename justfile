# =============================================================================
# justfile: A makefile-like build script -- parse_type
# =============================================================================
# REQUIRES: cargo install just
# PLATFORMS: Windows, Linux, macOS, ...
# USAGE:
#   just --list
#   just <TARGET>
#   just <TARGET> <PARAM_VALUE>
#
# SEE ALSO:
#   * https://github.com/casey/just
# =============================================================================

# -- OPTION: Load environment-variables from "$HERE/.env" file (if exists)
set dotenv-load

# -----------------------------------------------------------------------------
# CONFIG:
# -----------------------------------------------------------------------------
HERE := justfile_directory()
PIP_INSTALL_OPTIONS := env_var_or_default("PIP_INSTALL_OPTIONS", "--quiet")
PYTEST_OPTIONS := env_var_or_default("PYTEST_OPTIONS", "")


# -----------------------------------------------------------------------------
# BUILD RECIPES / TARGETS:
# -----------------------------------------------------------------------------

# DEFAULT-TARGET: Ensure that packages are installed and runs tests.
default: (_ensure-install-packages "testing") test

# PART=all, testing, ...
install-packages PART="all":
    @echo "INSTALL-PACKAGES: {{PART}} ..."
    pip install {{PIP_INSTALL_OPTIONS}} -r py.requirements/{{PART}}.txt
    @touch "{{HERE}}/.done.install-packages.{{PART}}"

# ENSURE: Python packages are installed.
_ensure-install-packages PART="all":
    #!/usr/bin/env python3
    from subprocess import run
    from os import path
    if not path.exists("{{HERE}}/.done.install-packages.{{PART}}"):
        run("just install-packages {{PART}}", shell=True)

# -- SIMILAR: This solution requires a Bourne-like shell (may not work on: Windows).
# _ensure-install-packages PART="testing":
#   @test -e "{{HERE}}/.done.install-packages.{{PART}}" || just install-packages {{PART}}

# Run tests.
test *TESTS:
    python -m pytest {{PYTEST_OPTIONS}} {{TESTS}}

# Determine test coverage by running the tests.
coverage:
    coverage run -m pytest
    coverage combine
    coverage report
    coverage html

# Cleanup most parts (but leave PRECIOUS parts).
cleanup: (_ensure-install-packages "all")
    invoke cleanup

# Cleanup everything.
cleanup-all:
    invoke cleanup.all
