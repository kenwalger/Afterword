"""Command-line entry point: `afterword probe` and `afterword baseline`.

Console output is limited to counts, statuses, IDs, and file paths. It never
includes comment text, commenter names, or the API key.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from afterword import baseline
from afterword.adapters.dev import records
from afterword.adapters.dev.client import ENV_VAR, DevClient, MissingCredentialError
from afterword.adapters.dev.probe import (
    FINDINGS_FILE,
    INDEX_FILE,
    Probe,
    ProbeLockedError,
    probe_lock,
)

RAW_ROOT = Path("fixtures/dev-api/source/real")
REPORT_ROOT = Path("reports")
LOCK_FILE = ".probe.lock"


def _run_dirs(root: Path) -> list[Path]:
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []


def _resolve_compare(root: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    probe_reports = root / REPORT_ROOT / "probe"
    if value == "latest":
        candidates = [p for p in _run_dirs(probe_reports) if (p / INDEX_FILE).exists()]
        if not candidates:
            raise SystemExit("--compare-to latest: no earlier run with a comment index")
        return candidates[-1]
    path = probe_reports / value
    if not (path / INDEX_FILE).exists():
        raise SystemExit(f"--compare-to: no comment index for run {value}")
    return path


def cmd_probe(args: argparse.Namespace) -> int:
    root = Path(args.root)
    compare = _resolve_compare(root, args.compare_to)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_dir = root / RAW_ROOT / run_id
    report_dir = root / REPORT_ROOT / "probe" / run_id
    try:
        client = DevClient.from_env(min_interval=args.min_interval)
    except MissingCredentialError:
        print(f"{ENV_VAR} is not set. It is read from the environment only.", file=sys.stderr)
        return 2
    lock = root / REPORT_ROOT / "probe" / LOCK_FILE
    try:
        with probe_lock(lock), client:
            probe = Probe(client, raw_dir, report_dir, run_id=run_id, page_size=args.page_size)
            findings = probe.run(article=args.article, compare_to=compare)
    except ProbeLockedError:
        print(
            f"another probe is running (lock file {lock}). "
            "If no probe is running, delete the lock file and retry.",
            file=sys.stderr,
        )
        return 3

    comments = findings.get("comments", {})
    print(f"run {run_id}: {findings['outcome']} (scope {findings['scope']})")
    print(
        f"requests sent: {findings['rate_limits']['requests_sent']}, "
        f"429s: {findings['rate_limits']['responses_429']}"
    )
    print(
        f"articles with comments fetched: {comments.get('articles_fetched', 0)}, "
        f"comment nodes: {comments.get('total_nodes', 0)}, "
        f"by content author: {comments.get('by_content_author', 0)}"
    )
    lifecycle = findings.get("lifecycle")
    if lifecycle:
        print(
            f"lifecycle vs {lifecycle['compared_to']}: added {len(lifecycle['added'])}, "
            f"removed {len(lifecycle['removed'])}, changed {len(lifecycle['changed'])}"
        )
    for item in findings["limitations"]:
        print(f"limitation: {item}")
    print(f"findings: {report_dir / FINDINGS_FILE}")
    return 0 if findings["outcome"] != "FAILED" else 1


def cmd_baseline(args: argparse.Namespace) -> int:
    # The run is always explicit, so a run containing test comments is never picked
    # up by default; the report records which run it came from.
    root = Path(args.root)
    run_file = root / RAW_ROOT / args.run / records.RUN_FILE
    if not run_file.exists():
        print(f"no probe run {args.run}", file=sys.stderr)
        return 2
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if run.get("scope") != "all" or run.get("outcome") == "FAILED":
        print(
            f"run {args.run} is scope {run.get('scope')}, outcome {run.get('outcome')}; "
            "the baseline needs a full-scope run that did not fail",
            file=sys.stderr,
        )
        return 2
    obs = records.load_run(run_file.parent)
    as_of = (obs.finished_at or datetime.now(UTC)).date()
    report = baseline.build(obs, as_of=as_of)
    out = root / REPORT_ROOT / f"baseline-{obs.run_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(baseline.render_markdown(report), encoding="utf-8")
    (root / REPORT_ROOT / f"baseline-{obs.run_id}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    t = report["totals"]
    print(
        f"articles {t['articles']}, comments {t['comments']} "
        f"(others {t['comments_from_others']}, author {t['comments_by_author']})"
    )
    print(f"report: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="afterword")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="read-only DEV capability probe")
    probe.add_argument(
        "--article", help="limit to one article: numeric ID or article URL (lifecycle tests)"
    )
    probe.add_argument("--compare-to", metavar="RUN_ID", help="earlier run ID, or 'latest'")
    probe.add_argument("--page-size", type=int, default=10, help="small page size for listing")
    probe.add_argument("--min-interval", type=float, default=1.0, help="seconds between requests")
    probe.set_defaults(func=cmd_probe)

    base = sub.add_parser("baseline", help="C-009 volume baseline from a probe run")
    base.add_argument("--run", required=True, help="full-scope probe run ID")
    base.set_defaults(func=cmd_baseline)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
