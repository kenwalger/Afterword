"""Model benchmark on the committed synthetic sets only (``afterword bench --synthetic``).

Measures, per model on this machine: seconds per comment cold and warm, the
schema-valid rate, malformed outputs by reason (unreadable or semantically
invalid), repeat stability at temperature 0, and, for the injection cases, the
EVALUATION pass condition (tier ``SURFACE``; the explanation is printed so a
human can check it does not repeat the injected instruction as reasoning).

Input is refused unless every file is listed in ``fixtures/corpus/MANIFEST.md``
as synthetic, its SHA-256 matches, and every record says ``provenance:
synthetic``. Output is synthetic data, counts, timings, and case IDs, so it is
safe to share. It is not a measure of classification quality and is never used
for tuning (``fixtures/corpus/MANIFEST.md``).
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from afterword import classifier, domain, policy, precheck, taxonomy
from afterword.normalize import normalize
from afterword.providers import Provider

CORPUS_DIR: Path = Path("fixtures/corpus")
MANIFEST: Path = CORPUS_DIR / "MANIFEST.md"
SETS: dict[str, str] = {
    "adversarial": "adversarial.jsonl",
    "synthetic-bench": "synthetic-bench.jsonl",
}
_ROW: re.Pattern[str] = re.compile(
    r"^\|\s*`(?P<file>[^`]+)`\s*\|\s*`(?P<set>[^`]+)`\s*\|\s*(?P<n>\d+)\s*\|"
    r"\s*(?P<prov>[a-z-]+)\s*\|\s*`(?P<sha>[0-9a-f]{64})`\s*\|"
)


class BenchRefused(Exception):
    """The input is not a verified synthetic set. The message is safe to print."""


def _manifest(root: Path) -> dict[str, dict[str, str]]:
    text = (root / MANIFEST).read_text(encoding="utf-8")
    return {
        m["file"]: m.groupdict()
        for line in text.splitlines()
        if (m := _ROW.match(line.strip())) is not None
    }


def load_cases(root: Path, sets: list[str]) -> list[dict[str, Any]]:
    """Load the named synthetic sets after checking them against the manifest.

    :param root: Repository root.
    :param sets: Set names from :data:`SETS`.
    :returns: Every case, set by set, in file order.
    :raises BenchRefused: For an unknown set, a file the manifest does not list as
        synthetic, a hash mismatch, or a record that is not synthetic.
    """
    manifest = _manifest(root)
    cases: list[dict[str, Any]] = []
    for name in sets:
        if name not in SETS:
            raise BenchRefused(f"{name} is not a synthetic set")
        entry = manifest.get(SETS[name])
        if entry is None or entry["prov"] != "synthetic" or entry["set"] != name:
            raise BenchRefused(f"{SETS[name]} is not listed as synthetic in the manifest")
        raw = (root / CORPUS_DIR / SETS[name]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha"]:
            raise BenchRefused(f"{SETS[name]} does not match its manifest hash")
        records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
        if len(records) != int(entry["n"]):
            raise BenchRefused(
                f"{SETS[name]} has {len(records)} records, manifest says {entry['n']}"
            )
        for r in records:
            if r.get("provenance") != "synthetic" or r.get("set") != name:
                raise BenchRefused(f"{SETS[name]}: case {r.get('case_id')} is not synthetic")
        cases += records
    return cases


def case_input(case: dict[str, Any]) -> tuple[classifier.ClassifierInput, str]:
    """Build the classifier input for one case, through the same normalization as a comment.

    :param case: A synthetic case.
    :returns: The input and the comment's normalized text.
    """
    fmt = case.get("body_source_format", "HTML")
    text = normalize(case["body_html"], fmt).text
    parent = case.get("parent")
    parent_text = None if parent is None else normalize(parent["body_html"], fmt).text
    inp = classifier.build_input(
        post_title=case.get("post_title"),
        comment=text,
        parent=parent_text,
        reply_to_author=bool(case.get("reply_to_author")),
    )
    return inp, text


def _tier(result: classifier.ModelResult, flags: frozenset[str]) -> policy.PriorityDecision:
    ok = result.outcome == domain.OK
    return policy.assign(
        policy.PolicyInput(
            outcome=result.outcome,
            primary_class=result.primary_class if ok else None,
            flags=flags,
            confidence=result.confidence if ok else None,
            edited_since_review=False,
        )
    )


def run_case(
    provider: Provider, case: dict[str, Any], clock: Callable[[], float] = time.monotonic
) -> dict[str, Any]:
    """Classify one case and apply the policy with and without the pre-check.

    :param provider: A verified provider.
    :param case: A synthetic case.
    :param clock: Monotonic clock.
    :returns: A JSON-ready record of the case's result.
    """
    inp, text = case_input(case)
    started = clock()
    result = classifier.classify(provider, inp)
    wall = clock() - started
    structural = {taxonomy.REPLY_TO_AUTHOR} if inp.reply_to_author else set()
    pre = precheck.precheck(text)
    pre_flags = {taxonomy.POSSIBLE_INSTRUCTION_TEXT} if pre.flagged else set()
    model_flags = set(result.flags)
    full = _tier(result, frozenset(model_flags | structural | pre_flags))
    without = _tier(result, frozenset(model_flags | structural))
    c = result.completion
    reason = (result.error or "").split(":", 1)[-1] if result.error else None
    return {
        "case_id": case["case_id"],
        "set": case["set"],
        "category": case.get("category"),
        "injection": bool(case.get("injection")),
        "intended_class": (case.get("intended") or {}).get("primary_class"),
        "outcome": result.outcome,
        "malformed_reason": reason if result.outcome == domain.MALFORMED else None,
        "failed_reason": reason if result.outcome == domain.FAILED else None,
        "primary_class": result.primary_class,
        "model_flags": sorted(model_flags),
        "confidence": result.confidence,
        "precheck_flagged": pre.flagged,
        "precheck_rules": list(pre.rules_matched),
        "tier": full.tier.name,
        "rule_applied": full.rule_applied,
        "tier_without_precheck": without.tier.name,
        "rule_without_precheck": without.rule_applied,
        "explanation": result.explanation,
        "wall_seconds": round(wall, 3),
        "latency_ms": result.latency_ms,
        "load_ms": None if c is None else c.load_ms,
        "input_tokens": None if c is None else c.input_tokens,
        "output_tokens": None if c is None else c.output_tokens,
        "stop_reason": None if c is None else c.stop_reason,
        "input_chars": len(classifier.SYSTEM_PROMPT) + len(classifier.render_user(inp)),
        "raw_output_sha256": None
        if result.raw_output is None
        else hashlib.sha256(result.raw_output.encode("utf-8")).hexdigest(),
    }


def _stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "p90": None, "max": None}
    ordered = sorted(values)
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 2),
        "median": round(statistics.median(values), 2),
        "p90": round(ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))], 2),
        "max": round(ordered[-1], 2),
    }


def summarize(results: list[dict[str, Any]], repeats: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize a run.

    :param results: Per-case records, in run order; the first is the cold start.
    :param repeats: Second runs of the first cases, for repeat stability.
    :returns: Counts, rates, timings, and the injection results.
    """
    n = len(results)
    outcomes = Counter(r["outcome"] for r in results)
    malformed = Counter(r["malformed_reason"] for r in results if r["malformed_reason"])
    warm = [r["wall_seconds"] for r in results[1:] if r["outcome"] != domain.FAILED]
    by_id = {r["case_id"]: r for r in results}
    same = sum(
        1 for r in repeats if r["raw_output_sha256"] == by_id[r["case_id"]]["raw_output_sha256"]
    )
    injections = [
        {
            "case_id": r["case_id"],
            "outcome": r["outcome"],
            "primary_class": r["primary_class"],
            "tier": r["tier"],
            "rule_applied": r["rule_applied"],
            "passes_tier": r["tier"] == policy.Tier.SURFACE.name,
            "tier_without_precheck": r["tier_without_precheck"],
            "precheck_flagged": r["precheck_flagged"],
            "model_flagged_instruction": taxonomy.POSSIBLE_INSTRUCTION_TEXT in r["model_flags"],
            "explanation": r["explanation"],
        }
        for r in results
        if r["injection"]
    ]
    known = [r for r in results if r["outcome"] == domain.OK and r["intended_class"]]
    return {
        "cases": n,
        "outcomes": dict(outcomes),
        "schema_valid": outcomes.get(domain.OK, 0),
        "schema_valid_rate": None if n == 0 else round(outcomes.get(domain.OK, 0) / n, 3),
        "malformed_unreadable": {
            k: v for k, v in malformed.items() if k in classifier.SYNTACTIC_REASONS
        },
        "malformed_semantic": {
            k: v for k, v in malformed.items() if k not in classifier.SYNTACTIC_REASONS
        },
        "failed": dict(Counter(r["failed_reason"] for r in results if r["failed_reason"])),
        "truncated": malformed.get("truncated", 0),
        "cold_seconds": results[0]["wall_seconds"] if results else None,
        "cold_load_ms": results[0]["load_ms"] if results else None,
        "warm_seconds_per_comment": _stats(warm),
        "max_input_tokens": max((r["input_tokens"] or 0 for r in results), default=0),
        "max_input_chars": max((r["input_chars"] for r in results), default=0),
        "max_output_tokens": max((r["output_tokens"] or 0 for r in results), default=0),
        "repeat_identical": same,
        "repeat_checked": len(repeats),
        "matches_intended_class_informational": sum(
            1 for r in known if r["primary_class"] == r["intended_class"]
        ),
        "tiers": dict(Counter(r["tier"] for r in results)),
        "injection_cases": injections,
        "injection_passing_tier": sum(1 for i in injections if i["passes_tier"]),
    }


def run_bench(
    provider: Provider,
    cases: list[dict[str, Any]],
    *,
    repeat: int = 3,
    progress: Callable[[int, int, dict[str, Any]], None] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Run every case once in order, then repeat the first few, and summarize.

    The model is unloaded first when the provider supports it, so the first
    case measures a cold start.

    :param provider: A verified provider.
    :param cases: Synthetic cases from :func:`load_cases`.
    :param repeat: How many of the first cases to run again.
    :param progress: Called after each case with its number, the total, and its record.
    :param clock: Monotonic clock.
    :returns: Per-case results, repeats, and the summary.
    """
    unload = getattr(provider, "unload", None)
    if callable(unload):
        unload()
    total = len(cases) + min(repeat, len(cases))
    results: list[dict[str, Any]] = []
    for i, case in enumerate(cases, start=1):
        results.append(run_case(provider, case, clock))
        if progress is not None:
            progress(i, total, results[-1])
    repeats: list[dict[str, Any]] = []
    for j, case in enumerate(cases[:repeat], start=len(cases) + 1):
        repeats.append(run_case(provider, case, clock))
        if progress is not None:
            progress(j, total, repeats[-1])
    return {"results": results, "repeats": repeats, "summary": summarize(results, repeats)}
