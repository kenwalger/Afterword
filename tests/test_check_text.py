from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_text  # noqa: E402

# Built from code points so this file contains none of the characters it tests.
DASH = chr(0x2014)
RLO = chr(0x202E)
LRI = chr(0x2066)
needs_tools = pytest.mark.skipif(
    shutil.which("git") is None or shutil.which("uv") is None, reason="git and uv required"
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


def make_repo(tmp_path: Path, hook: str) -> Path:
    """A throwaway repo with the real checker and only the named real hook."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REPO / "scripts" / "check_text.py", repo / "scripts" / "check_text.py")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    shutil.copy(REPO / "scripts" / "hooks" / hook, hooks / hook)
    git(repo, "init", "-q")
    git(repo, "config", "core.hooksPath", hooks.as_posix())
    return repo


def test_scan_counts_per_line():
    text = f"clean\na {DASH} b {DASH}\nmixed {RLO}x{LRI} {DASH}\n"
    assert check_text.scan(text) == [
        check_text.Finding(2, 2, 0),
        check_text.Finding(3, 1, 2),
    ]
    assert check_text.scan("plain ascii - and -- are fine\n") == []


def test_every_listed_bidi_control_is_caught():
    controls = [chr(c) for c in [*range(0x202A, 0x202F), *range(0x2066, 0x206A)]]
    assert len(controls) == 9
    for ch in controls:
        assert check_text.scan(f"x{ch}y") == [check_text.Finding(1, 0, 1)]


def test_report_shows_positions_and_counts_never_text():
    lines = check_text.report("a.md", check_text.scan(f"secret words {DASH} here"))
    assert lines == ["a.md:1: em-dash=1 bidi-control=0"]
    assert "secret" not in lines[0]


def test_message_mode(tmp_path):
    message = tmp_path / "MSG"
    message.write_text(f"Subject\n\nBody {DASH} text\n", encoding="utf-8")
    assert check_text.check_message(message) == ["commit message:3: em-dash=1 bidi-control=0"]
    assert check_text.main(["message", str(message)]) == 1
    message.write_text("Subject\n\nBody, text\n", encoding="utf-8")
    assert check_text.main(["message", str(message)]) == 0
    assert check_text.main([]) == 2


@pytest.mark.skipif(shutil.which("git") is None, reason="git required")
def test_staged_mode_checks_staged_content_and_exempts_license(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "clean.md").write_text("fine\n", encoding="utf-8")
    (repo / "bad.md").write_text(f"ok\nnot {DASH} ok\n", encoding="utf-8")
    (repo / "LICENSE").write_text(f"third-party {DASH} text\n", encoding="utf-8")
    (repo / "blob.bin").write_bytes(bytes([0xFF, 0xFE, 0x00, 0x14]))
    (repo / "later.md").write_text("clean when staged\n", encoding="utf-8")
    git(repo, "add", ".")
    # Only the staged version counts: an unstaged edit is not checked.
    (repo / "later.md").write_text(f"dirty {DASH}\n", encoding="utf-8")
    (repo / "untracked.md").write_text(f"{RLO}\n", encoding="utf-8")
    assert check_text.check_staged(cwd=repo) == ["bad.md:2: em-dash=1 bidi-control=0"]


@needs_tools
def test_pre_commit_hook_rejects_a_staged_em_dash(tmp_path):
    repo = make_repo(tmp_path, "pre-commit")
    (repo / "notes.md").write_text(f"line one\nhidden {DASH} words\n", encoding="utf-8")
    git(repo, "add", "notes.md")
    result = git(repo, "commit", "-q", "-m", "Add notes", check=False)
    assert result.returncode != 0
    assert "notes.md:2: em-dash=1 bidi-control=0" in result.stdout + result.stderr
    assert "hidden" not in result.stdout + result.stderr
    assert git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode != 0


@needs_tools
def test_commit_msg_hook_rejects_and_accepts(tmp_path):
    repo = make_repo(tmp_path, "commit-msg")
    (repo / "a.md").write_text("content\n", encoding="utf-8")
    git(repo, "add", "a.md")
    rejected = git(repo, "commit", "-q", "-m", f"Subject\n\nBody {DASH} more", check=False)
    assert rejected.returncode != 0
    assert "commit message:3: em-dash=1 bidi-control=0" in rejected.stdout + rejected.stderr
    accepted = git(repo, "commit", "-q", "-m", "Subject\n\nBody, more", check=False)
    assert accepted.returncode == 0, accepted.stderr
    assert git(repo, "log", "--format=%s").stdout.strip() == "Subject"
