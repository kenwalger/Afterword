"""Command-line entry point: `afterword probe`, `afterword baseline`, `afterword label`.

For `probe` and `baseline`, console output is limited to counts, statuses, IDs,
and file paths. It never includes comment text, commenter names, or the API
key. `label` is the exception by design: it shows comment text (never names)
in the author's own terminal, and is never run by an assistant session.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

from afterword import baseline, labeling
from afterword.adapters.dev import records
from afterword.adapters.dev.client import ENV_VAR, DevClient, MissingCredentialError
from afterword.adapters.dev.probe import (
    FINDINGS_FILE,
    INDEX_FILE,
    Probe,
    ProbeLockedError,
    probe_lock,
)

RAW_ROOT: Path = Path("fixtures/dev-api/source/real")
REPORT_ROOT: Path = Path("reports")
LOCK_FILE: str = ".probe.lock"


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
    """Run the read-only DEV probe.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
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


def _full_run(root: Path, run_id: str) -> Path | None:
    """Find a saved full-scope run that did not fail, printing why if there is none.

    :param root: Repository root.
    :param run_id: Probe run ID.
    :returns: The run's raw directory, or ``None``.
    """
    run_file = root / RAW_ROOT / run_id / records.RUN_FILE
    if not run_file.exists():
        print(f"no probe run {run_id}", file=sys.stderr)
        return None
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if run.get("scope") != "all" or run.get("outcome") == "FAILED":
        print(
            f"run {run_id} is scope {run.get('scope')}, outcome {run.get('outcome')}; "
            "this needs a full-scope run that did not fail",
            file=sys.stderr,
        )
        return None
    return run_file.parent


def cmd_baseline(args: argparse.Namespace) -> int:
    """Compute the C-009 baseline from an explicit full-scope run.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    # The run is always explicit, so a run containing test comments is never picked
    # up by default; the report records which run it came from.
    root = Path(args.root)
    run_dir = _full_run(root, args.run)
    if run_dir is None:
        return 2
    obs = records.load_run(run_dir)
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


def cmd_label(args: argparse.Namespace) -> int:
    """Label comments, or time a chronological review, from an explicit full-scope run.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    root = Path(args.root)
    if args.mode == "chronological" and not args.week:
        print("--mode chronological needs --week (any date in the week)", file=sys.stderr)
        return 2
    if not 1 <= args.batch_size <= labeling.MAX_BATCH:
        print(f"--batch-size must be 1 to {labeling.MAX_BATCH}", file=sys.stderr)
        return 2
    try:
        labeling.safe_name(args.corpus_version)
        labeling.safe_name(args.corpus_set)
        week = date.fromisoformat(args.week) if args.week else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    only_ids = None
    if args.ids:
        lines = Path(args.ids).read_text(encoding="utf-8").splitlines()
        only_ids = {line.strip() for line in lines if line.strip()}
    run_dir = _full_run(root, args.run)
    if run_dir is None:
        return 2

    # Comment text can hold any character; never crash the session on one.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")
    snap = labeling.Snapshot(records.load_run(run_dir, include_text=True))
    finished = snap.obs.finished_at
    if finished is None or datetime.now(UTC) - finished > labeling.STALE_AFTER:
        age = (
            "an unknown time" if finished is None else f"{(datetime.now(UTC) - finished).days} days"
        )
        print(
            f"warning: run {args.run} finished {age} ago. Comments deleted upstream since "
            "then are still shown (ADR-009). Run a fresh full probe before labeling."
        )
    excluded = snap.excluded_counts()
    print(
        f"run {args.run}: {len(snap.subjects())} comments to label; not labeled: "
        f"{excluded['by_author']} by the author, {excluded['deletion_placeholders']} deletion "
        f"placeholders, {excluded['unexpected_shapes']} unexpected shapes, "
        f"{excluded['undated']} undated"
    )
    if excluded["unexpected_shapes"]:
        print("warning: unexpected shapes need a friction entry before this run is used (ADR-009)")
    if only_ids is not None:
        known = {c.source_object_id for c in snap.subjects()}
        print(f"--ids: {len(only_ids & known)} of {len(only_ids)} IDs are labelable in this run")

    console = labeling.Console()
    if week is not None:
        labeling.run_chronological(snap, console, root=root, week=week)
        return 0
    labeling.run_labeling(
        snap,
        console,
        root=root,
        pass_name=args.pass_name,
        corpus_version=args.corpus_version,
        corpus_set=args.corpus_set,
        batch_size=args.batch_size,
        only_ids=only_ids,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    :returns: The parser, with one subcommand per tool.
    """
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

    label = sub.add_parser(
        "label", help="label comments, or time a chronological review (local terminal)"
    )
    label.add_argument("--run", required=True, help="full-scope probe run ID to read from")
    label.add_argument("--mode", choices=("label", "chronological"), default="label")
    label.add_argument("--week", help="chronological mode: any date (YYYY-MM-DD) in the week")
    label.add_argument(
        "--batch-size",
        type=int,
        default=labeling.MAX_BATCH,
        help=f"comments per batch, at most {labeling.MAX_BATCH}",
    )
    label.add_argument("--pass", dest="pass_name", choices=labeling.PASSES, default="initial")
    label.add_argument("--corpus-version", default=labeling.DEFAULT_CORPUS_VERSION)
    label.add_argument("--set", dest="corpus_set", default=labeling.DEFAULT_CORPUS_SET)
    label.add_argument("--ids", help="file of comment IDs to restrict to, one per line")
    label.set_defaults(func=cmd_label)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line.

    :param argv: Arguments, or ``None`` for ``sys.argv``.
    :returns: Process exit status.
    """
    args = build_parser().parse_args(argv)
    command: Callable[[argparse.Namespace], int] = args.func
    return command(args)


if __name__ == "__main__":
    raise SystemExit(main())
