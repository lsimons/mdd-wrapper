"""Entry point: the whole wrapper, in about ten lines of wiring.

`mdd.cli.build_dispatcher` takes exactly two extension points — the name
of the default mirror backend, and a list of extra command modules. A
wrapper registers whatever backends it provides, picks its default, and
gets the full `mdd` command line with no forking and no plugin discovery.

This one adds no subcommands, which makes it the minimal example: the
only difference from the open-source core is where a synced mirror gets
pushed.
"""

from __future__ import annotations

import os

from mdd.cli import build_dispatcher
from mdd.mirror import register_backend

from mdd_wrapper.backend import GitHubBackend

BACKEND_NAME = "github"

#: GitHub owner the mirrors live under. Overridable so the same wrapper
#: can be pointed at a fork without editing code.
DEFAULT_OWNER = "lsimons"


def owner() -> str:
    """Return the configured GitHub owner for mirrors."""
    return os.environ.get("MDD_WRAPPER_GITHUB_OWNER") or DEFAULT_OWNER


def main(argv: list[str] | None = None) -> int:
    """Run the `mdd` CLI with the GitHub backend wired as the default."""
    if BACKEND_NAME not in _registered():
        register_backend(BACKEND_NAME, GitHubBackend(owner()))
    parser = build_dispatcher(default_backend=BACKEND_NAME)
    ns = parser.parse_args(argv)
    func = getattr(ns, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return int(func(ns))  # pyright: ignore[reportAny]


def _registered() -> set[str]:
    from mdd.mirror import BACKENDS  # noqa: PLC0415  # read at call time, not import time

    return set(BACKENDS)


if __name__ == "__main__":
    raise SystemExit(main())
