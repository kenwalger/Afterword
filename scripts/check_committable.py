"""Check that no real identity data is about to be committed.

Loads every commenter handle and display name from the git-ignored raw probe
runs (through the DEV adapter, which alone knows the payload fields), plus the
author's own identity, then searches every file git would
commit (tracked, plus untracked files that are not ignored).

Prints counts per file only. Never prints a matched value.

Exception: the author's own handle, name, and email are allowed in
`pyproject.toml` (package metadata) and `NOTICE` (license attribution). Other
commenters' terms are enforced in every file, including those two. A commenter
term that is a whole word of the author's own identity (such as a shared first
name) counts as author identity, so it is allowed only in those two files.

Usage: uv run python scripts/check_committable.py
Runs as the pre-commit hook in scripts/hooks/ (install: git config core.hooksPath scripts/hooks).
Exit status: 0 if clean, 1 if any disallowed match.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from afterword.adapters.dev.records import identity_terms

RAW_ROOT: Path = Path("fixtures/dev-api/source/real")
# Files whose job is to name the author: package metadata and the license NOTICE.
AUTHOR_IDENTITY_ALLOWED_IN: frozenset[str] = frozenset({"pyproject.toml", "NOTICE"})
# Synthetic fixture addresses and documentation placeholders are not identities.
EMAIL_SHAPE: re.Pattern[str] = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SAFE_EMAIL_SUFFIXES: tuple[str, ...] = (".invalid", "@example.com")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout


def load_terms() -> tuple[set[str], set[str], set[str], int]:
    """Load the identity terms to search for.

    :returns: Author terms, other commenters' terms, author emails, and the number of raw runs read.
    """
    found = identity_terms(RAW_ROOT)
    author, others, emails = set(found.author), set(found.others), set(found.author_emails)
    git_email = _git("config", "user.email").strip()
    if git_email:
        emails.add(git_email)
    # A commenter term that is also a whole word of the author's own identity
    # (for example a shared first name) cannot tell the two apart. Treat it as
    # author identity: allowed only where author identity is allowed, and still
    # a violation in every other file.
    shared = {t for t in others if any(_word(t).search(a) for a in author)}
    return author | shared, others - author - shared, emails, found.runs_read


def _word(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")


def _pattern(terms: set[str]) -> re.Pattern[str] | None:
    if not terms:
        return None
    alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)")


def _count(pattern: re.Pattern[str] | None, text: str) -> int:
    return len(pattern.findall(text)) if pattern else 0


def main() -> int:
    """Scan every committable file and print counts per file.

    :returns: 0 if clean, 1 if any disallowed match.
    """
    author, others, emails, runs = load_terms()
    p_author, p_others, p_email = _pattern(author), _pattern(others), _pattern(emails)
    files = _git("ls-files", "--cached", "--others", "--exclude-standard").split()

    print(
        f"terms loaded from {runs} raw runs: author={len(author)} others={len(others)} "
        f"author_emails={len(emails)}"
    )
    if runs == 0:
        print("warning: no raw runs found; only author email and email-shape checks apply")
    print(f"files scanned: {len(files)}")

    violations = 0
    for name in files:
        path = Path(name)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        n_author = _count(p_author, text)
        n_others = _count(p_others, text)
        n_email = _count(p_email, text)
        n_shaped = sum(
            1
            for m in EMAIL_SHAPE.findall(text)
            if not m.endswith(SAFE_EMAIL_SUFFIXES) and not (p_email and p_email.fullmatch(m))
        )
        if not (n_author or n_others or n_email or n_shaped):
            continue
        allowed = name in AUTHOR_IDENTITY_ALLOWED_IN
        bad = n_others + n_shaped + (0 if allowed else n_author + n_email)
        violations += bad
        status = "VIOLATION" if bad else "allowed (author identity in metadata or NOTICE)"
        print(
            f"{name}: author_terms={n_author} other_terms={n_others} "
            f"author_email={n_email} other_email_shaped={n_shaped} -> {status}"
        )

    print(f"disallowed matches: {violations}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
