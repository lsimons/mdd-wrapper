"""Tests for the GitHub mirror backend."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest
from mdd.mirror import MirrorBackend, MirrorTarget
from mdd.mirror.errors import MirrorPushError

from mdd_wrapper.backend import GitHubBackend

if TYPE_CHECKING:
    from pathlib import Path


def test_satisfies_the_mirror_backend_protocol() -> None:
    """`GitHubBackend` must structurally satisfy `MirrorBackend`.

    This is the drift alarm. `MirrorBackend` is a `Protocol`, so nothing
    forces a backend to declare conformance and a method added upstream
    goes unnoticed until it is called at runtime. Annotating the
    assignment makes basedpyright check the whole surface, so the next
    method the core adds fails `mise run typecheck` here — unless
    `GenericGitBackend` supplies it, which is the case where inheriting
    the default is the right answer anyway.
    """
    backend: MirrorBackend = GitHubBackend("lsimons")
    assert backend is not None


def _repo_with_origin(path: Path, origin: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _ = subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "remote", "add", "origin", origin], cwd=path, check=True, capture_output=True
    )
    return path


class TestResolveRemote:
    def test_uses_the_target_key_as_the_repo_name(self) -> None:
        backend = GitHubBackend("lsimons")
        url = backend.resolve_remote(MirrorTarget(kind="confluence", key="MDD"))
        assert url == "https://github.com/lsimons/MDD.git"

    def test_per_kind_override_wins(self) -> None:
        backend = GitHubBackend("lsimons", repo_for={"confluence": "test-confluence-MDD"})
        url = backend.resolve_remote(MirrorTarget(kind="confluence", key="MDD"))
        assert url == "https://github.com/lsimons/test-confluence-MDD.git"

    def test_a_kind_without_an_override_still_falls_back(self) -> None:
        backend = GitHubBackend("lsimons", repo_for={"confluence": "pinned"})
        url = backend.resolve_remote(MirrorTarget(kind="sharepoint", key="Engineering"))
        assert url == "https://github.com/lsimons/Engineering.git"


class TestEnsureRemote:
    def test_assumes_the_repository_exists(self) -> None:
        outcome = GitHubBackend("lsimons").ensure_remote(MirrorTarget(kind="confluence", key="MDD"))
        assert outcome.status == "exists"
        assert outcome.remote_url == "https://github.com/lsimons/MDD.git"


class TestGuardRemote:
    def test_allows_a_matching_https_origin(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "m", "https://github.com/lsimons/mirror.git")
        GitHubBackend("lsimons").guard_remote(repo)

    def test_allows_a_matching_ssh_origin(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "m", "git@github.com:lsimons/mirror.git")
        GitHubBackend("lsimons").guard_remote(repo)

    def test_owner_match_is_case_insensitive(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "m", "https://github.com/LSimons/mirror.git")
        GitHubBackend("lsimons").guard_remote(repo)

    def test_refuses_a_different_owner(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "m", "https://github.com/someone-else/mirror.git")
        with pytest.raises(MirrorPushError, match="only writes to"):
            GitHubBackend("lsimons").guard_remote(repo)

    def test_refuses_a_different_host(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "m", "https://gitlab.example.com/lsimons/mirror.git")
        with pytest.raises(MirrorPushError, match="only writes to"):
            GitHubBackend("lsimons").guard_remote(repo)

    def test_refuses_a_lookalike_host(self, tmp_path: Path) -> None:
        """`github.com.attacker.example` must not pass as `github.com`."""
        repo = _repo_with_origin(
            tmp_path / "m", "https://github.com.attacker.example/lsimons/mirror.git"
        )
        with pytest.raises(MirrorPushError, match="only writes to"):
            GitHubBackend("lsimons").guard_remote(repo)

    def test_refuses_an_origin_the_parser_does_not_recognise(self, tmp_path: Path) -> None:
        """A remote that is neither scp-like nor http(s) cannot be shown to be ours."""
        repo = _repo_with_origin(tmp_path / "m", "/srv/git/mirror.git")
        with pytest.raises(MirrorPushError, match="only writes to"):
            GitHubBackend("lsimons").guard_remote(repo)

    def test_refuses_a_worktree_with_no_origin(self, tmp_path: Path) -> None:
        repo = tmp_path / "m"
        repo.mkdir()
        _ = subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
        with pytest.raises(MirrorPushError, match="no 'origin' remote"):
            GitHubBackend("lsimons").guard_remote(repo)


class TestReachable:
    def test_is_always_true(self) -> None:
        assert GitHubBackend("lsimons").reachable() is True


class TestWebUrl:
    """The browse URL the Confluence footer links to (GitHub's `/blob/` shape)."""

    def test_blob_url_for_a_mirror_clone(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "mirror", "https://github.com/lsimons/MDD.git")
        page = repo / "Home" / "My Page.md"
        page.parent.mkdir()
        _ = page.write_text("# My Page\n", encoding="utf-8")

        url = GitHubBackend("lsimons").web_url(page)

        assert url == "https://github.com/lsimons/MDD/blob/main/Home/My%20Page.md"

    def test_none_for_a_work_tree_on_another_host(self, tmp_path: Path) -> None:
        repo = _repo_with_origin(tmp_path / "mirror", "git@gitlab.example.com:g/MDD.git")
        page = repo / "Page.md"
        _ = page.write_text("# Page\n", encoding="utf-8")

        assert GitHubBackend("lsimons").web_url(page) is None

    def test_none_outside_a_git_work_tree(self, tmp_path: Path) -> None:
        page = tmp_path / "Page.md"
        _ = page.write_text("# Page\n", encoding="utf-8")

        assert GitHubBackend("lsimons").web_url(page) is None
