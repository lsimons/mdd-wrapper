"""Tests for the wrapper entry point."""

from __future__ import annotations

import contextlib
import io
from typing import TYPE_CHECKING

from mdd.mirror import default_backend, default_backend_name

from mdd_wrapper.backend import GitHubBackend
from mdd_wrapper.cli import BACKEND_NAME, main, owner

if TYPE_CHECKING:
    import pytest


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
