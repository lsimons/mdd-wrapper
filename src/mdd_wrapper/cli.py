"""Entry point: the whole wrapper, in about ten lines of wiring.

`mdd` exposes the composition seam as three calls a wrapper makes before
handing control back:

- :func:`mdd.mirror.register_backend` — add a mirror backend;
- :func:`mdd.commands.register_skill_root` — add a directory of bundled
  Claude Code skills;
- :func:`mdd.cli.build_dispatcher` — build the argparse tree, choosing the
  default backend, any extra command modules, and what ``--version``
  prints.

:func:`mdd.cli.run` then parses, applies the root logging flags and
dispatches. Using it rather than hand-rolling ``parse_args`` is what keeps
``-v``, ``--trace`` and ``--log-level`` working: those flags configure
logging inside ``run``, so a wrapper that parses for itself silently
accepts and ignores them.

This one adds no subcommands, which makes it the minimal example: the
only differences from the core are where a synced mirror gets pushed and
one extra bundled skill.
"""

from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path

import mdd
from mdd.cli import build_dispatcher, run
from mdd.commands import register_skill_root
from mdd.mirror import register_backend

from mdd_wrapper import __version__
from mdd_wrapper.backend import GitHubBackend

BACKEND_NAME = "github"

#: GitHub owner the mirrors live under. Overridable so the same wrapper
#: can be pointed at a fork without editing code.
DEFAULT_OWNER = "lsimons"


def owner() -> str:
    """Return the configured GitHub owner for mirrors."""
    return os.environ.get("MDD_WRAPPER_GITHUB_OWNER") or DEFAULT_OWNER


def version_string() -> str:
    """Return what ``mdd --version`` prints.

    Both versions, because both matter: this distribution is the one the
    user installed and the one a bug report is filed against, while the
    core supplies every command they actually ran.
    """
    return f"mdd-wrapper {__version__} (mdd {mdd.__version__})"


def skills_root() -> Path:
    """Return this distribution's bundled-skills directory.

    Resolved through ``importlib.resources`` so it works from a source
    tree and from an installed wheel alike; ``pyproject.toml`` ships the
    directory as package data for the latter.
    """
    return Path(str(files("mdd_wrapper") / "skills"))


def main(argv: list[str] | None = None) -> int:
    """Run the `mdd` CLI with the GitHub backend and skills wired in."""
    if BACKEND_NAME not in _registered():
        register_backend(BACKEND_NAME, GitHubBackend(owner()))
        # Guarded by the same flag: the skill root is appended to a
        # module-level list, so registering twice in one process would
        # list this bundle twice.
        register_skill_root(skills_root())
    parser = build_dispatcher(default_backend=BACKEND_NAME, version=version_string())
    return run(parser, argv)


def _registered() -> set[str]:
    from mdd.mirror import BACKENDS  # noqa: PLC0415  # read at call time, not import time

    return set(BACKENDS)


if __name__ == "__main__":
    raise SystemExit(main())
