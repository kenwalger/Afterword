"""Check that no real identity data is about to be committed.

Loads every commenter handle and display name from the git-ignored raw probe
runs, plus the author's own identity, then searches every file git would
commit (tracked, plus untracked files that are not ignored).

Prints counts per file only. Never prints a matched value.

Exception: the author's own handle, name, and email are allowed in
`pyproject.toml` (package metadata). Other commenters' terms are enforced in
every file, including `pyproject.toml`. A commenter term that is a whole word
of the author's own identity (such as a shared first name) counts as author
identity, so it is allowed only in `pyproject.toml`.

Usage: uv run python scripts/check_committable.py
Exit status: 0 if clean, 1 if any disallowed match.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

RAW_ROOT = Path("fixtures/dev-api/source/real")
USER_FIELDS = ("username", "name", "github_username", "twitter_username")
AUTHOR_IDENTITY_ALLOWED_IN = frozenset({"pyproject.toml"})
# Synthetic fixture addresses and documentation placeholders are not identities.
EMAIL_SHAPE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SAFE_EMAIL_SUFFIXES = (".invalid", "@example.com")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout


def _iter_users(value: object):
    stack = [value]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            if isinstance(v.get("user"), dict):
                yield v["user"]
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)


def load_terms() -> tuple[set[str], set[str], set[str], int]:
    """Return (author terms, other commenters' terms, author emails, runs read)."""
    author, others, emails = set(), set(), set()
    runs = 0
    if RAW_ROOT.exists():
        for run_dir in sorted(p for p in RAW_ROOT.iterdir() if p.is_dir()):
            me_path = run_dir / "users-me.json"
            if not me_path.exists():
                continue
            runs += 1
            me = json.loads(me_path.read_text(encoding="utf-8"))["response"]["body"]
            me_id = me.get("id") if isinstance(me, dict) else None
            if isinstance(me, dict) and isinstance(me.get("email"), str):
                emails.add(me["email"])
            for path in run_dir.glob("*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                body = record.get("response", {}).get("body") if isinstance(record, dict) else None
                for user in _iter_users(body):
                    target = (
                        author if me_id is not None and user.get("user_id") == me_id else others
                    )
                    for field in USER_FIELDS:
                        value = user.get(field)
                        if isinstance(value, str) and value.strip():
                            target.add(value.strip())
    git_email = _git("config", "user.email").strip()
    if git_email:
        emails.add(git_email)
    # A commenter term that is also a whole word of the author's own identity
    # (for example a shared first name) cannot tell the two apart. Treat it as
    # author identity: allowed only where author identity is allowed, and still
    # a violation in every other file.
    shared = {t for t in others if any(_pattern({t}).search(a) for a in author)}
    return author | shared, others - author - shared, emails, runs


def _pattern(terms: set[str]) -> re.Pattern[str] | None:
    if not terms:
        return None
    alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)")


def _count(pattern: re.Pattern[str] | None, text: str) -> int:
    return len(pattern.findall(text)) if pattern else 0


def main() -> int:
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
        status = "VIOLATION" if bad else "allowed (author identity in package metadata)"
        print(
            f"{name}: author_terms={n_author} other_terms={n_others} "
            f"author_email={n_email} other_email_shaped={n_shaped} -> {status}"
        )

    print(f"disallowed matches: {violations}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
