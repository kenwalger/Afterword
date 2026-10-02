"""Reject em-dashes and bidi control characters in commits.

Two modes, one per git hook:

- ``staged``: check the staged content of every added, copied, modified, or
  renamed file (pre-commit). ``LICENSE`` is exempt: it is verbatim
  third-party text.
- ``message FILE``: check a commit message (commit-msg).

Prints counts and ``file:line`` positions only, never the offending text.
The characters are built from code points, so this file contains none of them.

Usage: uv run python scripts/check_text.py staged
       uv run python scripts/check_text.py message .git/COMMIT_EDITMSG
Exit status: 0 if clean, 1 if any forbidden character, 2 for bad usage.
"""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

EM_DASH: str = chr(0x2014)
# Bidi embedding, override, and isolate controls: U+202A to U+202E, U+2066 to U+2069.
BIDI_CONTROLS: frozenset[str] = frozenset(
    chr(c) for c in [*range(0x202A, 0x202F), *range(0x2066, 0x206A)]
)
EXEMPT_PATHS: frozenset[str] = frozenset({"LICENSE"})


@dataclass(frozen=True)
class Finding:
    """Forbidden characters on one line."""

    line: int
    em_dashes: int
    bidi_controls: int


def scan(text: str) -> list[Finding]:
    """Find lines containing em-dashes or bidi control characters.

    :param text: Text to check.
    :returns: One finding per offending line, in line order.
    """
    findings = []
    for number, line in enumerate(text.split("\n"), start=1):
        counts = Counter(ch for ch in line if ch == EM_DASH or ch in BIDI_CONTROLS)
        if counts:
            dashes = counts.pop(EM_DASH, 0)
            findings.append(Finding(number, dashes, sum(counts.values())))
    return findings


def report(label: str, findings: list[Finding]) -> list[str]:
    """Format findings as positions and counts only.

    :param label: File path or ``commit message``.
    :param findings: Output of :func:`scan`.
    :returns: One line per finding.
    """
    return [
        f"{label}:{f.line}: em-dash={f.em_dashes} bidi-control={f.bidi_controls}" for f in findings
    ]


def _git(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True, cwd=cwd).stdout


def staged_paths(cwd: Path | None = None) -> list[str]:
    """List staged files whose content is being added or changed.

    :param cwd: Repository directory; the current directory when ``None``.
    :returns: Paths relative to the repository root.
    """
    out = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z", cwd=cwd)
    return [p for p in out.decode("utf-8").split("\0") if p]


def check_staged(cwd: Path | None = None) -> list[str]:
    """Check the staged version of every changed file, skipping binaries and exempt paths.

    :param cwd: Repository directory; the current directory when ``None``.
    :returns: Report lines for every offending line.
    """
    lines = []
    for path in staged_paths(cwd):
        if path in EXEMPT_PATHS:
            continue
        try:
            text = _git("show", f":{path}", cwd=cwd).decode("utf-8")
        except UnicodeDecodeError:
            continue  # binary content
        lines.extend(report(path, scan(text)))
    return lines


def check_message(path: Path) -> list[str]:
    """Check a commit message file.

    :param path: The message file git passes to the commit-msg hook.
    :returns: Report lines for every offending line.
    """
    return report("commit message", scan(path.read_text(encoding="utf-8", errors="replace")))


def main(argv: list[str] | None = None) -> int:
    """Run one check mode.

    :param argv: Arguments without the program name; ``sys.argv[1:]`` when ``None``.
    :returns: 0 if clean, 1 if any forbidden character, 2 for bad usage.
    """
    args = sys.argv[1:] if argv is None else argv
    if args == ["staged"]:
        lines = check_staged()
    elif len(args) == 2 and args[0] == "message":
        lines = check_message(Path(args[1]))
    else:
        print("usage: check_text.py staged | message FILE", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    if lines:
        print(
            f"rejected: {len(lines)} line(s) with em-dashes or bidi control characters. "
            "Use a colon, comma, parentheses, or a new sentence instead of an em-dash."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
