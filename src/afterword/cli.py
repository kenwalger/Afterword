"""Command-line entry point: `probe`, `baseline`, `label`, `label-ui`, and later commands.

The CLI is a transport (ADR-012): it parses arguments, calls
:mod:`afterword.service`, and formats what comes back.

For `probe` and `baseline`, console output is limited to counts, statuses, IDs,
times, and file paths. It never includes comment text, commenter names, or the
API key. `label` is the exception by design: it shows comment text (never names)
in the author's own terminal, and is never run by an assistant session; `label-ui`
shows it only in a page served on 127.0.0.1, and prints counts and its URL.
`label status` prints progress counts only, with no class or grade distribution.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from afterword import baseline, bench, heuristic, label_ui, labeling, policy, service
from afterword.progress import StatusLine
from afterword.providers import ollama

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
    for line in baseline.console_summary(result.report):
        print(line)
    print()
    print(f"Full report, with weekly and monthly tables: {result.markdown_path}")
    return 0


def _open_labeling(args: argparse.Namespace) -> service.LabelingSession | int:
    """Validate the shared labeling options, open the run, and print its counts.

    :param args: Parsed arguments of ``label`` or ``label-ui``.
    :returns: The opened run, or a process exit status on failure.
    """
    if not 1 <= args.batch_size <= labeling.MAX_BATCH:
        print(f"--batch-size must be 1 to {labeling.MAX_BATCH}", file=sys.stderr)
        return 2
    if args.posts == "random" and args.seed is None:
        print("--posts random needs --seed N, so the order can be resumed", file=sys.stderr)
        return 2
    try:
        labeling.safe_name(args.corpus_version)
        labeling.safe_name(args.corpus_set)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        session = service.open_for_labeling(Path(args.root), args.run)
    except service.ServiceError as exc:
        return _fail(exc)
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
    return session


def _only_ids(args: argparse.Namespace, session: service.LabelingSession) -> set[str] | None:
    if not args.ids:
        return None
    lines = Path(args.ids).read_text(encoding="utf-8").splitlines()
    only_ids = {line.strip() for line in lines if line.strip()}
    known = service.labelable_ids(session)
    print(f"--ids: {len(only_ids & known)} of {len(only_ids)} IDs are labelable in this run")
    return only_ids


def _id_file(path: str | None) -> set[str] | None:
    if not path:
        return None
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip()}


def cmd_label(args: argparse.Namespace) -> int:
    """Label comments, or time a chronological review, from an explicit full-scope run.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    root = Path(args.root)
    if args.action == "status":
        return cmd_label_status(args)
    if args.mode == "chronological" and not args.week:
        print("--mode chronological needs --week (any date in the week)", file=sys.stderr)
        return 2
    try:
        week = date.fromisoformat(args.week) if args.week else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    opened = _open_labeling(args)
    if isinstance(opened, int):
        return opened
    session = opened
    # Comment text can hold any character; never crash the session on one.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")
    only_ids = _only_ids(args, session)

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
        post_order=args.posts,
        seed=args.seed,
    )
    return 0


def cmd_label_status(args: argparse.Namespace) -> int:
    """Print labeling progress for a run: counts only, no classes, grades, IDs, or text.

    :param args: Parsed arguments of ``label status``.
    :returns: Process exit status.
    """
    opened = _open_labeling(args)
    if isinstance(opened, int):
        return opened
    try:
        counts = service.label_progress(
            opened, root=Path(args.root), corpus_version=args.corpus_version
        )
    except service.ServiceError as exc:
        return _fail(exc)
    by_pass = ", ".join(f"{name} {n}" for name, n in counts.by_pass.items())
    by_tool = ", ".join(f"{name} {n}" for name, n in counts.by_tool.items())
    by_order = ", ".join(
        f"{name} {n}" for name, n in counts.by_post_order.items() if n or name != "unknown"
    )
    print(f"corpus version {args.corpus_version}: {counts.eligible} eligible comments")
    print(f"labeled {counts.labeled}, remaining {counts.remaining} (pass initial)")
    print(f"labeled comments by pass: {by_pass}")
    print(f"labels by tool: {by_tool}")
    print(f"labels by post order: {by_order}")
    if counts.not_in_run:
        print(f"labeled comments not eligible in this run: {counts.not_in_run}")
    return 0


def cmd_label_ui(args: argparse.Namespace) -> int:
    """Label comments in a local browser page served on 127.0.0.1.

    The terminal shows counts, the session URL, and the end summary; comment
    text appears only in the page.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    opened = _open_labeling(args)
    if isinstance(opened, int):
        return opened
    session = opened
    ui = label_ui.LabelUI(
        session=session,
        root=Path(args.root),
        options=label_ui.BatchOptions(
            pass_name=args.pass_name,
            corpus_version=args.corpus_version,
            corpus_set=args.corpus_set,
            batch_size=args.batch_size,
            only_ids=_only_ids(args, session),
            post_order=args.posts,
            seed=args.seed,
        ),
    )
    ui.start_batch()
    if ui.batch is None:
        print(f"Nothing left to label in pass {args.pass_name}.")
        return 0
    try:
        server = label_ui.create_server(ui, port=args.port)
    except OSError as exc:
        print(f"cannot listen on 127.0.0.1:{args.port}: {exc.strerror}", file=sys.stderr)
        ui.stop()
        return 2
    print(f"batch {ui.batch.context().batch_id}: {len(ui.batch.items)} comments")
    print(f"open: {server.url}")
    print("Stop with q in the page, or Ctrl+C here. Saved labels are kept either way.")
    if not args.no_browser:
        webbrowser.open(server.url)
    server.serve()
    print(f"stopped: {ui.labeled_total} labeled in {ui.batches_started} batch(es)")
    return 0


def _labeling_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run", required=True, help="full-scope probe run ID to read from")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=labeling.MAX_BATCH,
        help=f"comments per batch, at most {labeling.MAX_BATCH}",
    )
    parser.add_argument("--pass", dest="pass_name", choices=labeling.PASSES, default="initial")
    parser.add_argument("--corpus-version", default=labeling.DEFAULT_CORPUS_VERSION)
    parser.add_argument("--set", dest="corpus_set", default=labeling.DEFAULT_CORPUS_SET)
    parser.add_argument("--ids", help="file of comment IDs to restrict to, one per line")
    parser.add_argument(
        "--posts",
        choices=labeling.POST_ORDERS,
        default="published",
        help="post order: by publication time (default) or shuffled by --seed; "
        "comments within a post are always oldest first",
    )
    parser.add_argument("--seed", type=int, help="seed for --posts random (recorded in the batch)")


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest one saved probe run into the local store.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        result = service.ingest_run(Path(args.root), args.run, keep_runs=args.keep_runs)
    except service.ServiceError as exc:
        return _fail(exc)
    made = " (new connection)" if result.created_connection else ""
    print(f"run {result.sync_run_id} ingested into connection {result.connection_id}{made}")
    counts = ", ".join(f"{k} {v}" for k, v in sorted(result.counts.items())) or "nothing"
    print(f"comments: {counts}")
    for item in result.limitations:
        print(f"limitation: {item}")
    if result.counts.get("unexpected_shapes"):
        print("warning: unexpected shapes need a friction entry before this run is used (ADR-009)")
    saved = result.saved_runs
    print(f"saved runs: deleted comments redacted {saved.withdrawn_redactions} (counted per run)")
    if saved.runs_reduced:
        print(f"saved runs reduced to structure (retention): {', '.join(saved.runs_reduced)}")
    if saved.runs_kept_for_labels:
        print(
            f"saved runs kept whole, labels made from them: {', '.join(saved.runs_kept_for_labels)}"
        )
    return 0


def cmd_store_status(args: argparse.Namespace) -> int:
    """Print a connection's comments by lifecycle state and its lifecycle events.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        status = service.store_status(Path(args.root), args.connection)
    except service.NoStoreError as exc:
        print(str(exc))
        return 0
    except service.ServiceError as exc:
        return _fail(exc)
    for section in ("comments", "events", "content_check"):
        print(f"{section}:")
        for key, n in status[section].items():
            print(f"  {key}: {n}")
    return 0


def cmd_connections(args: argparse.Namespace) -> int:
    """List the store's platform connections with record counts.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        summaries = service.list_connections(Path(args.root))
    except service.NoStoreError as exc:
        print(str(exc))
        return 0
    if not summaries:
        print("no connections")
    for s in summaries:
        c = s.connection
        print(
            f"{c.connection_id}  {c.platform}  created {c.created_at.isoformat()}  "
            f"runs {s.counts['sync_runs']}, posts {s.counts['content_items']}, "
            f"comments {s.counts['comments']}, classifications {s.counts['classifications']}"
        )
    return 0


def cmd_forget(args: argparse.Namespace) -> int:
    """Remove all local data for one connection; without --yes, only count it.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        counts = service.forget_connection(Path(args.root), args.connection, confirm=args.yes)
    except service.NoStoreError as exc:
        print(str(exc))
        return 0
    except service.ServiceError as exc:
        return _fail(exc)
    rows = ", ".join(f"{k} {v}" for k, v in counts.items())
    if not args.yes:
        print(f"would delete: {rows}")
        print("nothing deleted; repeat with --yes to delete")
        return 1
    print(f"deleted: {rows}")
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    """Classify the store's comments from others with B1 or B2, then apply the policy.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    status = StatusLine()
    status.start(f"classify {args.condition}")
    try:
        result = service.classify_comments(
            Path(args.root),
            condition=args.condition,
            provider_name=args.provider,
            model=args.model,
            connection_id=args.connection,
            host=args.ollama_host,
            heuristic_version=args.heuristic,
            only_ids=_id_file(args.ids),
            progress=lambda done, total: status.step("classify", done, total),
        )
    except service.ServiceError as exc:
        status.finish(f"classify {args.condition}")
        return _fail(exc)
    status.finish(f"classify {args.condition}")
    digest = f" digest {result.model_digest[:12]}" if result.model_digest else ""
    print(
        f"{result.condition}: {result.model_provider} {result.model_id}{digest} "
        f"on connection {result.connection_id}"
    )
    print(
        f"comments {result.subjects}: classified {result.classified}, "
        f"reused from cache {result.reused}"
    )
    print("outcomes: " + ", ".join(f"{k} {v}" for k, v in sorted(result.outcomes.items())))
    if result.errors:
        print("errors: " + ", ".join(f"{k} {v}" for k, v in sorted(result.errors.items())))
    print("tiers: " + ", ".join(f"{k} {v}" for k, v in sorted(result.tiers.items())))
    return 0


def _pct(share: dict[str, Any]) -> str:
    if share["share"] is None:
        return f"{share['count']} of {share['of']}"
    low, high = share["wilson95"]
    return (
        f"{share['count']} of {share['of']} ({100 * share['share']:.1f}%; "
        f"Wilson {100 * low:.1f}% to {100 * high:.1f}%)"
    )


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Score cached classifications against the dev labels under one policy, offline.

    Prints counts only. The full counts go to a git-ignored JSON report, and with
    ``--misses`` the IDs of consequential comments collapsed go to a git-ignored
    list for the author's own review.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        result = service.evaluate_condition(
            Path(args.root),
            condition=args.condition,
            policy_version=args.policy,
            heuristic_version=args.heuristic,
            provider_name=args.provider,
            model=args.model,
            corpus_version=args.corpus_version,
            only_ids=_id_file(args.ids),
            num_ctx=args.num_ctx,
            connection_id=args.connection,
        )
    except service.ServiceError as exc:
        return _fail(exc)
    report, misses = service.write_evaluation_report(
        Path(args.root), result, with_misses=args.misses
    )
    print(
        f"{result.condition} {result.model_provider} {result.model_id} under "
        f"{result.policy_version}: {result.scored} of {result.labels} labeled comments scored"
        + (f" (not scored: {result.not_scored})" if result.not_scored else "")
    )
    for order, s in result.scores.items():
        if not s["total"]:
            continue
        tiers = s["by_tier"]
        print(
            f"  {order}: consequential surfaced {_pct(s['consequential_recall'])}; "
            f"collapsed {_pct(s['review_reduction'])}; "
            f"SURFACE {tiers['SURFACE']}, QUEUE {tiers['QUEUE']}, COLLAPSED {tiers['COLLAPSED']}"
        )
    print(f"report: {report}")
    if misses is not None:
        print(f"miss list (IDs only, {len(result.missed_ids)}): {misses}")
    return 0


def cmd_dev_analysis(args: argparse.Namespace) -> int:
    """Count tier causes, class confusion, and languages on the dev set, offline.

    Writes the counts to a git-ignored JSON report and prints a short summary.
    Counts only: no text, IDs, or names.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        result = service.analyze_dev(
            Path(args.root),
            model=args.model,
            provider_name=args.provider,
            num_ctx=args.num_ctx,
            heuristic_version=args.heuristic,
            corpus_version=args.corpus_version,
            connection_id=args.connection,
        )
    except service.ServiceError as exc:
        return _fail(exc)
    path = service.write_dev_analysis(Path(args.root), result)
    pre = result.precheck
    print(
        f"{result.subjects} comments from others, {result.labels} labeled; pre-check "
        f"{pre['version']} fired on {pre['fired']} ({pre['labeled']} labeled, "
        f"{pre['labeled_consequential']} graded 2 or 3)"
    )
    print(f"languages ({result.language['detector']}): {result.language['by_language']}")
    print(f"report: {path}")
    return 0


def cmd_dev_subset(args: argparse.Namespace) -> int:
    """Choose a seeded, class-balanced subset of labeled dev comments and write its IDs.

    Prints counts only; the IDs go to a git-ignored file for ``--ids``.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    try:
        subset = service.select_dev_subset(
            Path(args.root), size=args.size, seed=args.seed, corpus_version=args.corpus_version
        )
    except service.ServiceError as exc:
        return _fail(exc)
    path = service.write_dev_subset(Path(args.root), subset)
    classes = ", ".join(f"{k} {v}" for k, v in subset.by_class.items() if v)
    print(f"dev subset: {subset.size} labeled comments, seed {subset.seed}")
    print(f"by class: {classes}")
    print(f"graded 2 or 3: {subset.consequential}; by post order: {subset.by_post_order}")
    print(f"IDs: {path}")
    return 0


def cmd_models_verify(args: argparse.Namespace) -> int:
    """Check each approved local model's installed digest against its pin.

    :param args: Parsed arguments.
    :returns: Process exit status: 0 when every model matches.
    """
    try:
        checks = service.verify_models(host=args.ollama_host)
    except service.ServiceError as exc:
        return _fail(exc)
    for c in checks:
        installed = c.installed[:12] if c.installed else "-"
        print(f"{c.status:<8} {c.model}  pinned {c.pinned[:12]}  installed {installed}")
    return 0 if all(c.status == "OK" for c in checks) else 1


def _bench_line(done: int, total: int, r: dict[str, Any]) -> None:
    detail = r["primary_class"] or r["malformed_reason"] or r["failed_reason"] or "-"
    tokens = f"{r['input_tokens'] or '-'}/{r['output_tokens'] or '-'}"
    print(
        f"[{done:>2}/{total}] {r['case_id']:<10} {r['outcome']:<9} {detail:<28} "
        f"{r['tier']:<9} {r['wall_seconds']:>7.2f}s  tokens in/out {tokens}",
        flush=True,
    )


def cmd_bench(args: argparse.Namespace) -> int:
    """Benchmark one model on the committed synthetic sets only.

    Output is synthetic data, counts, timings, and case IDs, so it is safe to share.

    :param args: Parsed arguments.
    :returns: Process exit status.
    """
    sets = args.set or list(bench.DEFAULT_SETS)
    print(f"bench: {args.provider} {args.model or ''} on {', '.join(sets)} (synthetic only)")
    try:
        result = service.run_benchmark(
            Path(args.root),
            synthetic=args.synthetic,
            provider_name=args.provider,
            model=args.model,
            sets=sets,
            repeat=args.repeat,
            host=args.ollama_host,
            progress=_bench_line,
        )
    except service.ServiceError as exc:
        return _fail(exc)
    r, s = result.report, result.report["summary"]
    warm = s["warm_seconds_per_comment"]
    print()
    print(f"model: {r['provider']} {r['model_id']} digest {r['model_digest'] or 'n/a'}")
    print(
        f"versions: {r['prompt_version']} {r['taxonomy_version']} {r['normalization_version']} "
        f"{r['precheck_version']} {r['policy_version']}; options {json.dumps(r['options'])}"
    )
    print(f"started {r['started_at']}, finished {r['finished_at']}")
    print(f"cases {s['cases']}; outcomes {json.dumps(s['outcomes'])}")
    print(f"schema-valid {s['schema_valid']} of {s['cases']} ({s['schema_valid_rate']})")
    print(
        f"malformed, unreadable: {json.dumps(s['malformed_unreadable'])}; "
        f"semantic: {json.dumps(s['malformed_semantic'])}; failed: {json.dumps(s['failed'])}"
    )
    print(f"cold: {s['cold_seconds']}s (model load {s['cold_load_ms']} ms)")
    print(
        f"warm seconds per comment: mean {warm['mean']}, median {warm['median']}, "
        f"p90 {warm['p90']}, max {warm['max']} (n {warm['n']})"
    )
    print(
        f"max input tokens {s['max_input_tokens']} ({s['max_input_chars']} chars), "
        f"max output tokens {s['max_output_tokens']}"
    )
    print(f"repeat stability: {s['repeat_identical']} of {s['repeat_checked']} identical")
    print(f"tiers: {json.dumps(s['tiers'])}")
    print(
        f"matches intended class (informational only): {s['matches_intended_class_informational']}"
    )
    print(
        f"injection cases at SURFACE: {s['injection_passing_tier']} of {len(s['injection_cases'])}"
    )
    for i in s["injection_cases"]:
        print(
            f"  {i['case_id']}: {i['outcome']} {i['primary_class'] or '-'} -> {i['tier']} "
            f"({i['rule_applied']}); without pre-check {i['tier_without_precheck']}; "
            f"pre-check {'yes' if i['precheck_flagged'] else 'no'}, "
            f"model flag {'yes' if i['model_flagged_instruction'] else 'no'}"
        )
        print(f"    explanation: {json.dumps(i['explanation'])}")
    print(f"report: {result.report_path}")
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
    label.add_argument(
        "action",
        nargs="?",
        choices=("status",),
        help="status: print labeling progress for the run (counts only) and exit",
    )
    _labeling_options(label)
    label.add_argument("--mode", choices=("label", "chronological"), default="label")
    label.add_argument("--week", help="chronological mode: any date (YYYY-MM-DD) in the week")
    label.set_defaults(func=cmd_label)

    ui = sub.add_parser("label-ui", help="label comments in a local browser page (127.0.0.1 only)")
    _labeling_options(ui)
    ui.add_argument("--port", type=int, default=label_ui.DEFAULT_PORT, help="0 picks a free port")
    ui.add_argument("--no-browser", action="store_true", help="print the URL only")
    ui.set_defaults(func=cmd_label_ui)

    ingest = sub.add_parser("ingest", help="ingest a saved probe run into the local store")
    ingest.add_argument("--run", required=True, help="probe run ID (ingest oldest first)")
    ingest.add_argument(
        "--keep-runs",
        type=int,
        default=service.KEEP_RUNS,
        help="saved runs kept whole; older ones are reduced to structure (default: %(default)s)",
    )
    ingest.set_defaults(func=cmd_ingest)

    conns = sub.add_parser("connections", help="list platform connections in the store")
    conns.set_defaults(func=cmd_connections)

    status = sub.add_parser(
        "store-status", help="counts by lifecycle state and lifecycle events (counts only)"
    )
    status.add_argument("--connection", help="connection ID (default: the only one)")
    status.set_defaults(func=cmd_store_status)

    forget = sub.add_parser("forget", help="remove all local data for one connection")
    forget.add_argument("--connection", required=True, help="connection ID")
    forget.add_argument("--yes", action="store_true", help="delete; without it, only count")
    forget.set_defaults(func=cmd_forget)

    host_help = "Ollama base URL; loopback only"
    classify = sub.add_parser("classify", help="classify stored comments with B1 or B2")
    classify.add_argument("--condition", required=True, choices=service.CONDITIONS)
    classify.add_argument("--provider", choices=service.PROVIDERS, default="ollama")
    classify.add_argument("--model", help="model ID (B2)")
    classify.add_argument("--connection", help="connection ID; optional with one connection")
    classify.add_argument("--ollama-host", default=ollama.DEFAULT_HOST, help=host_help)
    classify.add_argument(
        "--heuristic",
        choices=list(heuristic.HEURISTIC_VERSIONS),
        default=heuristic.HEURISTIC_VERSION,
        help="heuristic version (B1)",
    )
    classify.add_argument("--ids", help="file of comment IDs to restrict to, one per line")
    classify.set_defaults(func=cmd_classify)

    evaluate = sub.add_parser(
        "evaluate", help="score cached classifications against the dev labels (counts only)"
    )
    evaluate.add_argument("--condition", required=True, choices=service.CONDITIONS)
    evaluate.add_argument("--policy", choices=policy.POLICY_VERSIONS, default=policy.POLICY_VERSION)
    evaluate.add_argument(
        "--heuristic",
        choices=list(heuristic.HEURISTIC_VERSIONS),
        default=heuristic.HEURISTIC_VERSION,
        help="heuristic version (B1)",
    )
    evaluate.add_argument("--provider", choices=service.PROVIDERS, default="ollama")
    evaluate.add_argument("--model", help="model ID (B2)")
    evaluate.add_argument("--corpus-version", default=labeling.DEFAULT_CORPUS_VERSION)
    evaluate.add_argument("--ids", help="file of comment IDs to restrict to, one per line")
    evaluate.add_argument(
        "--num-ctx",
        type=int,
        help="Ollama B2: score runs made with this context size (default: the current one)",
    )
    evaluate.add_argument("--connection", help="connection ID; optional with one connection")
    evaluate.add_argument(
        "--misses",
        action="store_true",
        help="also write the IDs of consequential comments collapsed (git-ignored)",
    )
    evaluate.set_defaults(func=cmd_evaluate)

    analysis = sub.add_parser(
        "dev-analysis", help="tier causes, class confusion, and languages on dev (counts only)"
    )
    analysis.add_argument("--model", required=True, help="B2 model ID")
    analysis.add_argument("--provider", choices=service.PROVIDERS, default="ollama")
    analysis.add_argument(
        "--num-ctx", type=int, help="Ollama B2: the context size its runs used (default: current)"
    )
    analysis.add_argument(
        "--heuristic", choices=list(heuristic.HEURISTIC_VERSIONS), default="hb-v0.2"
    )
    analysis.add_argument("--corpus-version", default=labeling.DEFAULT_CORPUS_VERSION)
    analysis.add_argument("--connection", help="connection ID; optional with one connection")
    analysis.set_defaults(func=cmd_dev_analysis)

    subset = sub.add_parser(
        "dev-subset", help="seeded, class-balanced subset of labeled dev comments (IDs to a file)"
    )
    subset.add_argument("--size", type=int, default=50, help="40 to 60")
    subset.add_argument("--seed", type=int, required=True)
    subset.add_argument("--corpus-version", default=labeling.DEFAULT_CORPUS_VERSION)
    subset.set_defaults(func=cmd_dev_subset)

    models = sub.add_parser("models", help="local model checks")
    models_sub = models.add_subparsers(dest="models_command", required=True)
    verify = models_sub.add_parser("verify", help="check installed digests against the pins")
    verify.add_argument("--ollama-host", default=ollama.DEFAULT_HOST, help=host_help)
    verify.set_defaults(func=cmd_models_verify)

    bench_cmd = sub.add_parser("bench", help="benchmark a model on the synthetic sets only")
    bench_cmd.add_argument(
        "--synthetic", action="store_true", help="required: confirms synthetic input only"
    )
    bench_cmd.add_argument("--provider", choices=service.PROVIDERS, default="ollama")
    bench_cmd.add_argument("--model", help="model ID")
    bench_cmd.add_argument(
        "--set", action="append", choices=list(bench.SETS), help="a synthetic set (default: both)"
    )
    bench_cmd.add_argument("--repeat", type=int, default=3, help="cases run twice (stability)")
    bench_cmd.add_argument("--ollama-host", default=ollama.DEFAULT_HOST, help=host_help)
    bench_cmd.set_defaults(func=cmd_bench)
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
