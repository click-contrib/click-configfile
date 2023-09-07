# -*- coding: UTF-8 -*-
"""
Invoke test tasks.
"""

from __future__ import print_function
from invoke import task, Collection
import os.path
import sys

# -- TASK-LIBRARY:
from invoke_cleanup import cleanup_tasks, cleanup_dirs, cleanup_files


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------
@task(name="all", help={
    "args": "Command line args for test run.",
})
def test_all(ctx, args="", options=""):
    """Run all tests (default)."""
    pytest_args = select_by_prefix(args, ctx.pytest.scopes)
    pytest_should_run = not args or (args and pytest_args)
    if pytest_should_run:
        pytest(ctx, pytest_args, options=options)

    behave_args = select_by_prefix(args, ctx.behave_test.scopes)
    behave_should_run = not args or (args and behave_args)
    if False and behave_should_run:
         behave(ctx, behave_args, options=options)


@task
def clean(ctx, dry_run=False):
    """Cleanup (temporary) test artifacts."""
    directories = ctx.test.clean.directories or []
    files = ctx.test.clean.files or []
    cleanup_dirs(directories, dry_run=dry_run)
    cleanup_files(files, dry_run=dry_run)


@task(name="unit")
def unittest(ctx, args="", options=""):
    """Run unit tests."""
    pytest(ctx, args, options)


@task
def pytest(ctx, args="", options=""):
    """Run unit tests."""
    args = args or ctx.pytest.args
    options = options or ctx.pytest.options
    ctx.run("pytest {options} {args}".format(options=options, args=args))


@task(help={
    "args": "Command line args for behave",
    "format": "Formatter to use (progress, pretty, ...)",
})
def behave(ctx, args="", format="", options=""):
    """Run behave tests."""
    format  = format or ctx.behave_test.format
    options = options or ctx.behave_test.options
    args = args or ctx.behave_test.args
    if os.path.exists("bin/behave"):
        behave = "{python} bin/behave".format(python=sys.executable)
    else:
        behave = "{python} -m behave".format(python=sys.executable)

    for group_args in grouped_by_prefix(args, ctx.behave_test.scopes):
        ctx.run("{behave} -f {format} {options} {args}".format(
            behave=behave, format=format, options=options, args=group_args))

@task(help={
    "args":     "Command line args for test",
    "report":   "Coverage report format to use (report, html, xml)",
})
def coverage(ctx, args="", report="report", append=False, combine=True):
    append = append or ctx.coverage.append
    combine = combine or ctx.coverage.combine
    report_formats = ctx.coverage.report_formats or []
    if report not in report_formats:
        report_formats.insert(0, report)
    opts = []
    if append:
        opts.append("--append")

    ctx.run("coverage run -m pytest {options} {args}".format(
            args=args, options=" ".join(opts)))
    if combine:
        ctx.run("coverage combine")
    for report_format in report_formats:
        ctx.run("coverage {report_format}".format(report_format=report_format))


# ---------------------------------------------------------------------------
# UTILITIES:
# ---------------------------------------------------------------------------
def select_prefix_for(arg, prefixes):
    for prefix in prefixes:
        if arg.startswith(prefix):
            return prefix
    return os.path.dirname(arg)

def select_by_prefix(args, prefixes):
    selected = []
    for arg in args.strip().split():
        assert not arg.startswith("-"), "REQUIRE: arg, not options"
        scope = select_prefix_for(arg, prefixes)
        if scope:
            selected.append(arg)
    return " ".join(selected)

def grouped_by_prefix(args, prefixes):
    """Group behave args by (directory) scope into multiple test-runs."""
    group_args = []
    current_scope = None
    for arg in args.strip().split():
        assert not arg.startswith("-"), "REQUIRE: arg, not options"
        scope = select_prefix_for(arg, prefixes)
        if scope != current_scope:
            if group_args:
                # -- DETECTED GROUP-END:
                yield " ".join(group_args)
                group_args = []
            current_scope = scope
        group_args.append(arg)
    if group_args:
        yield " ".join(group_args)


# ---------------------------------------------------------------------------
# TASK MANAGEMENT / CONFIGURATION
# ---------------------------------------------------------------------------
namespace = Collection(clean, unittest, pytest, coverage)
namespace.add_task(test_all, default=True)
namespace.configure({
    "test": {
        "clean": {
            "directories": [
                ".cache", "assets",                         # -- TEST RUNS
                "__WORKDIR__", "reports", "test_results",   # -- BEHAVE test
            ],
            "files": [
                ".coverage", ".coverage.*",
                "report.html",
                "rerun*.txt", "rerun*.featureset", "testrun*.json",
            ],
        },
    },
    "pytest": {
        "scopes":   ["tests"],
        "args":   "",
        "options": "",  # -- NOTE:  Override in configfile "invoke.yaml"
    },
    # "behave_test": behave.namespace._configuration["behave_test"],
    "behave_test": {
        "scopes":   ["features", "issue.features"],
        "args":     "features issue.features",
        "format":   "progress",
        "options":  "",  # -- NOTE:  Override in configfile "invoke.yaml"
    },
    "coverage": {
        "append":   False,
        "combine":  True,
        "report_formats": ["report", "html"],
    },
})

# -- ADD CLEANUP TASK:
cleanup_tasks.add_task(clean, "clean_test")
cleanup_tasks.configure(namespace.configuration())
