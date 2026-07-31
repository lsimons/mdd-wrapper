"""Tests for the wrapper entry point."""

from __future__ import annotations

import contextlib
import io
import logging
import os
from typing import TYPE_CHECKING

import mdd
import pytest
from mdd.commands import skill_roots
from mdd.mirror import default_backend, default_backend_name

import mdd_wrapper
from mdd_wrapper.backend import GitHubBackend
from mdd_wrapper.cli import BACKEND_NAME, main, owner, skills_root, version_string

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def restored_core_logger() -> Iterator[logging.Logger]:
    """Undo what `mdd.cli.run` does to the shared `mdd` logger.

    The core configures logging as a process-wide side effect, so a test
    that exercises the root flags has to put the logger back or it leaks
    a level and a stderr handler into every later test.
    """
    logger = logging.getLogger("mdd")
    level, handlers = logger.level, list(logger.handlers)
    try:
        yield logger
    finally:
        logger.setLevel(level)
        logger.handlers = handlers


class TestOwner:
    def test_defaults_to_the_project_owner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MDD_WRAPPER_GITHUB_OWNER", raising=False)
        assert owner() == "lsimons"

    def test_environment_overrides_the_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MDD_WRAPPER_GITHUB_OWNER", "someone-else")
        assert owner() == "someone-else"


class TestMain:
    def test_no_args_prints_help_and_succeeds(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert main([]) == 0
        assert "usage: mdd" in buf.getvalue()

    def test_wires_the_github_backend_as_the_default(self) -> None:
        _ = main([])
        assert isinstance(default_backend(), GitHubBackend)

    def test_ships_the_core_commands(self) -> None:
        """The wrapper adds no subcommands; it inherits the full core set."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _ = main([])
        out = buf.getvalue()
        for command in ("convert", "confluence", "sharepoint", "search", "ai"):
            assert command in out

    def test_adds_no_site_specific_commands(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _ = main([])
        out = buf.getvalue()
        assert "gitlab" not in out
        assert "lucid" not in out

    def test_registration_is_idempotent(self) -> None:
        """Two invocations in one process must not trip the duplicate-key guard."""
        _ = main([])
        _ = main([])
        assert default_backend_name() == BACKEND_NAME


class TestVersion:
    def test_names_this_distribution_first(self) -> None:
        """The version a user cares about is the one they installed."""
        assert version_string().startswith(f"mdd-wrapper {mdd_wrapper.__version__}")

    def test_also_reports_the_core(self) -> None:
        assert f"(mdd {mdd.__version__})" in version_string()

    def test_the_flag_prints_it(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), pytest.raises(SystemExit) as exit_info:
            _ = main(["--version"])
        assert exit_info.value.code == 0
        assert buf.getvalue().strip() == version_string()


class TestLoggingFlags:
    """Dispatching through `mdd.cli.run` is what makes the root flags work.

    A wrapper that calls `parse_args` itself accepts `-v` / `--trace` and
    then silently ignores them, because the core applies them in `run`.
    """

    def test_verbose_configures_the_core_logger(self, restored_core_logger: logging.Logger) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            _ = main(["-vv", "echo", "hi"])
        assert restored_core_logger.getEffectiveLevel() == logging.DEBUG

    def test_trace_bodies_sets_the_core_environment_flag(
        self, monkeypatch: pytest.MonkeyPatch, restored_core_logger: logging.Logger
    ) -> None:
        _ = restored_core_logger
        monkeypatch.delenv("MDD_TRACE_BODIES", raising=False)
        with contextlib.redirect_stdout(io.StringIO()):
            _ = main(["--trace-bodies", "echo", "hi"])
        assert os.environ.get("MDD_TRACE_BODIES") == "1"


class TestSkillRoot:
    def test_the_bundled_skills_directory_is_registered(self) -> None:
        _ = main([])
        assert skills_root() in skill_roots()

    def test_the_core_root_still_comes_first(self) -> None:
        """Last-registered wins, so the wrapper must not displace the core bundle."""
        _ = main([])
        assert skill_roots()[0] != skills_root()

    def test_registration_is_not_repeated(self) -> None:
        _ = main([])
        _ = main([])
        assert [r for r in skill_roots() if r == skills_root()] == [skills_root()]

    def test_the_bundle_contains_a_skill(self) -> None:
        skills = sorted(p.name for p in skills_root().iterdir() if (p / "SKILL.md").is_file())
        assert skills == ["mdd-wrapper-mirror-skill"]
