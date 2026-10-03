"""Command-line entry point: `afterword probe`, `afterword baseline`, `afterword label`.

The CLI is a transport (ADR-012): it parses arguments, calls
:mod:`afterword.service`, and formats what comes back.

For `probe` and `baseline`, console output is limited to counts, statuses, IDs,
times, and file paths. It never includes comment text, commenter names, or the
API key. `label` is the exception by design: it shows comment text (never names)
in the author's own terminal, and is never run by an assistant session.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

from afterword import labeling, service
from afterword.progress import StatusLine

# Kept here for callers and tests that locate outputs through the CLI.
RAW_ROOT: Path = service.RAW_ROOT
REPORT_ROOT: Path = service.REPORT_ROOT
LOCK_FILE: str = service.LOCK_FILE


def _fail(error: service.ServiceError) -> int:
    print(str(error), file=sys.stderr)
    return error.code


def cmd_probe(args: argparse.Namespace) -> int:
    """Run the read-only DEV probe, with a status line and start, end, and elapsed times.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    status = StatusLine()
    hooks = service.ProbeHooks(
        request=status.request,
        wait=status.wait,
        step=status.step,
        started=lambda run_id: status.start(f"probe run {run_id}"),
        finished=lambda run_id: status.finish(f"probe run {run_id}"),
    )
    try:
        result = service.run_probe(
            Path(args.root),
            article=args.article,
            compare_to=args.compare_to,
            page_size=args.page_size,
            min_interval=args.min_interval,
            hooks=hooks,
        )
    except service.ServiceError as exc:
        return _fail(exc)

    findings = result.findings
    comments = findings.get("comments", {})
    print(f"run {result.run_id}: {findings['outcome']} (scope {findings['scope']})")
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
    print(f"findings: {result.findings_path}")
    return 0 if findings["outcome"] != "FAILED" else 1


def cmd_baseline(args: argparse.Namespace) -> int:
    """Compute the C-009 baseline from an explicit full-scope run.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        exclude = [date.fromisoformat(d) for d in args.exclude_week or []]
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        result = service.build_baseline(Path(args.root), args.run, exclude_weeks=exclude)
    except service.ServiceError as exc:
        return _fail(exc)
    t = result.report["totals"]
    print(
        f"articles {t['articles']}, comments {t['comments']} "
        f"(others {t['comments_from_others']}, author {t['comments_by_author']})"
    )
    rt = result.report["review_timing"]
    print(
        f"valid review timings: {len(rt['valid'])}, "
        f"practice or unconfirmed ignored: {rt['ignored']}"
    )
    replacement = result.report["replacement_typical_week"]
    if replacement:
        week = replacement["week"]
        print(
            "replacement typical week: "
            + (
                f"{week['week_start']} ({week['comments_from_others']} comments from others)"
                if week
                else "none"
            )
        )
    print(f"report: {result.markdown_path}")
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
    try:
        session = service.open_for_labeling(root, args.run)
    except service.ServiceError as exc:
        return _fail(exc)

    # Comment text can hold any character; never crash the session on one.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")
    if session.stale:
        age = "an unknown time" if session.age is None else f"{session.age.days} days"
        print(
            f"warning: run {args.run} finished {age} ago. Comments deleted upstream since "
            "then are still shown (ADR-009). Run a fresh full probe before labeling."
        )
    excluded = session.excluded
    print(
        f"run {args.run}: {session.subjects} comments to label; not labeled: "
        f"{excluded['by_author']} by the author, {excluded['deletion_placeholders']} deletion "
        f"placeholders, {excluded['unexpected_shapes']} unexpected shapes, "
        f"{excluded['undated']} undated"
    )
    if excluded["unexpected_shapes"]:
        print("warning: unexpected shapes need a friction entry before this run is used (ADR-009)")
    if only_ids is not None:
        known = service.labelable_ids(session)
        print(f"--ids: {len(only_ids & known)} of {len(only_ids)} IDs are labelable in this run")

    console = labeling.Console()
    if week is not None:
        service.time_week(session, console, root=root, week=week)
        return 0
    service.label_batch(
        session,
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
    base.add_argument(
        "--exclude-week",
        action="append",
        metavar="DATE",
        help="a week already re-read (any date in it); repeat for each. With this, the "
        "report names the replacement typical week closest to the trailing-13 median",
    )
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
