"""The frozen corpus: export records, their committed manifest, and verification.

A corpus version (``v1``, ``v2``, ...) is written once, at preregistration, as
one git-ignored JSONL file per set under ``fixtures/corpus/<version>/``
(``fixtures/README.md``, "Corpus record"), with comment text. Its manifest,
committed under ``registry/``, holds only IDs and hashes: the file's SHA-256 and
each record's, with the comment and post IDs. A changed hash means a new corpus
version.

A comment deleted upstream after the freeze is withdrawn from the corpus file
at the next ingest (ADR-009): its text goes, its ID stays, and the record says
it was withdrawn. Verification reports withdrawn records apart from records
that changed for any other reason. A record counts as withdrawn only when its
text is gone and everything else in it still matches the manifest's hash of the
record without its text.

Each file is written once, and rewritten only by a withdrawal, which writes
beside the file and swaps it in, so an interrupted write never truncates the
only frozen copy of the text.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

CORPUS_ROOT: Path = Path("fixtures/corpus")
MANIFEST_ROOT: Path = Path("registry")
PROVENANCE: str = "public-real"
_VERSION: re.Pattern[str] = re.compile(r"^v[1-9][0-9]*$")
# Added to a record by an ADR-009 withdrawal, with ``body_text`` set to null.
WITHDRAWAL_FIELDS: tuple[str, ...] = ("withdrawn", "withdrawn_on")
RECORD_FIELDS: tuple[str, ...] = (
    "comment_id",
    "source_object_id",
    "content_id",
    "corpus_set",
    "body_text",
    "parent_comment_id",
    "context_as_of",
    "provenance",
    "normalization_version",
)


def is_version(name: str) -> bool:
    """Report whether a name is a corpus version (``v1``, ``v2``, ...).

    :param name: A directory or version name.
    :returns: ``True`` for ``v`` followed by a positive integer.
    """
    return bool(_VERSION.match(name))


def check_version(version: str) -> str:
    """Check a corpus version name.

    :param version: A name such as ``v1``.
    :returns: The name.
    :raises ValueError: Unless it is ``v`` followed by a positive integer, the form
        the git-ignore rule (``fixtures/corpus/v*/``) covers.
    """
    if not _VERSION.match(version):
        raise ValueError(f"corpus version must look like v1, v2, ...: {version!r}")
    return version


def data_path(version: str, corpus_set: str) -> Path:
    """Return the git-ignored corpus file of one set.

    :param version: Corpus version.
    :param corpus_set: ``dev`` or ``test``.
    :returns: ``fixtures/corpus/<version>/<set>.jsonl``, relative to the repository root.
    """
    return CORPUS_ROOT / check_version(version) / f"{corpus_set}.jsonl"


def manifest_path(version: str, corpus_set: str) -> Path:
    """Return the committed manifest of one set.

    :param version: Corpus version.
    :param corpus_set: ``dev`` or ``test``.
    :returns: ``registry/corpus-<version>-<set>.json``, relative to the repository root.
    """
    return MANIFEST_ROOT / f"corpus-{check_version(version)}-{corpus_set}.json"


def line_of(record: dict[str, Any]) -> str:
    """Serialize one corpus record the one way it is hashed.

    :param record: A corpus record.
    :returns: Compact JSON with sorted keys, without a line ending.
    """
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(record: dict[str, Any]) -> str:
    """Return the SHA-256 of one record's serialized line.

    :param record: A corpus record.
    :returns: Lower-case hex digest.
    """
    return hashlib.sha256(line_of(record).encode("utf-8")).hexdigest()


def metadata_hash(record: dict[str, Any]) -> str:
    """Return the SHA-256 of a record without its text or withdrawal fields.

    A withdrawal changes only those fields, so this hash is the same before and after it.

    :param record: A corpus record, withdrawn or not.
    :returns: Lower-case hex digest.
    """
    dropped = {"body_text", *WITHDRAWAL_FIELDS}
    return record_hash({k: v for k, v in record.items() if k not in dropped})


def file_bytes(records: list[dict[str, Any]]) -> bytes:
    """Serialize a corpus file: records sorted by comment ID, one per line, LF.

    :param records: Corpus records.
    :returns: UTF-8 bytes.
    """
    ordered = sorted(records, key=lambda r: str(r["comment_id"]))
    return "".join(f"{line_of(r)}\n" for r in ordered).encode("utf-8")


def manifest(
    records: list[dict[str, Any]],
    *,
    version: str,
    corpus_set: str,
    created_at: str,
    store_as_of: str | None,
    registered_at: str | None,
) -> dict[str, Any]:
    """Build a corpus manifest: IDs and hashes only, never text.

    :param records: The corpus records, as written.
    :param version: Corpus version.
    :param corpus_set: ``dev`` or ``test``.
    :param created_at: When the corpus was frozen (RFC 3339, UTC).
    :param store_as_of: The latest probe run ingested into the store it came from.
    :param registered_at: The preregistration time, or ``None`` before it.
    :returns: The manifest.
    """
    data = file_bytes(records)
    return {
        "corpus_version": version,
        "corpus_set": corpus_set,
        "created_at": created_at,
        "registered_at": registered_at,
        "store_as_of_sync_run": store_as_of,
        "normalization_versions": sorted({str(r["normalization_version"]) for r in records}),
        "provenance": PROVENANCE,
        "file": data_path(version, corpus_set).as_posix(),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "records": len(records),
        "comments": [
            {
                "comment_id": r["comment_id"],
                "content_id": r["content_id"],
                "record_sha256": record_hash(r),
                "metadata_sha256": metadata_hash(r),
            }
            for r in sorted(records, key=lambda r: str(r["comment_id"]))
        ],
    }


def read_records(path: Path) -> list[dict[str, Any]]:
    """Read a corpus file.

    Lines end at LF only: ``str.splitlines`` would also split at U+2028, U+2029,
    and U+0085, which the serialization leaves unescaped inside text.

    :param path: A corpus file.
    :returns: Its records.
    """
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line]


def write_once(path: Path, data: bytes) -> None:
    """Create a file with these bytes; never replace one.

    An existing file is left as it was (``FileExistsError``). If writing fails,
    the partly written file is removed and the error raised.

    :param path: The file to create; its parent directory is created if needed.
    :param data: Its content.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("xb")
    written = False
    try:
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        written = True
    finally:
        if not written:
            # Created by the open above, so a partial file is this call's to remove.
            path.unlink(missing_ok=True)


def _replace(path: Path, data: bytes) -> None:
    # Written beside the file, then swapped in (as adapters/dev/redact.py does).
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@dataclass(frozen=True)
class CorpusCheck:
    """A corpus file checked against its manifest. Counts only."""

    records: int
    matched: int
    withdrawn: int
    changed: int
    missing: int
    extra: int
    file_matches: bool
    duplicates: int = 0
    # Whether the manifest's registered_at equals the preregistration record's
    # (both absent counts as equal); set by the caller, which reads the record.
    registered_at_matches: bool = True

    @property
    def ok(self) -> bool:
        """Report whether every record matches its manifest entry or was withdrawn under ADR-009.

        Without a withdrawal the file must also match the manifest's file hash;
        a withdrawal changes that hash, so it is checked record by record then.
        The manifest's ``registered_at`` must equal the record's.

        :returns: ``True`` when nothing changed, went missing, was added, or was
            repeated, the file hash matches unless a record was withdrawn, and
            ``registered_at`` matches.
        """
        records_ok = not (self.changed or self.missing or self.extra or self.duplicates)
        file_ok = self.file_matches or self.withdrawn > 0
        return records_ok and file_ok and self.registered_at_matches


def _withdrawn(record: dict[str, Any], entry: dict[str, Any]) -> bool:
    """Report whether a record is its frozen self with only an ADR-009 withdrawal applied."""
    return (
        record.get("withdrawn") is True
        and record.get("body_text", "") is None
        and isinstance(record.get("withdrawn_on"), str)
        and metadata_hash(record) == entry.get("metadata_sha256")
    )


def check(entries: list[dict[str, Any]], file_sha256: str, path: Path) -> CorpusCheck:
    """Compare a corpus file with its manifest's entries.

    :param entries: The manifest's ``comments``.
    :param file_sha256: The manifest's ``file_sha256``.
    :param path: The corpus file.
    :returns: Counts of matched, withdrawn, changed, missing, extra, and repeated
        records, and whether the file hash matches.
    """
    lines = read_records(path) if path.exists() else []
    ids = Counter(str(r["comment_id"]) for r in lines)
    records = {str(r["comment_id"]): r for r in lines}
    expected = {str(e["comment_id"]): e for e in entries}
    matched = withdrawn = changed = 0
    for comment_id, entry in expected.items():
        record = records.get(comment_id)
        if record is None:
            continue
        if record_hash(record) == entry["record_sha256"]:
            matched += 1
        elif _withdrawn(record, entry):
            withdrawn += 1
        else:
            changed += 1
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
    return CorpusCheck(
        records=len(records),
        matched=matched,
        withdrawn=withdrawn,
        changed=changed,
        missing=sum(1 for c in expected if c not in records),
        extra=sum(1 for c in records if c not in expected),
        file_matches=actual == file_sha256,
        duplicates=sum(n - 1 for n in ids.values()),
    )


def withdraw(path: Path, withdrawn: set[str], *, on: date) -> list[str]:
    """Withdraw deleted comments from one corpus file (ADR-009): text out, ID kept.

    :param path: A corpus file.
    :param withdrawn: Source IDs of comments deleted upstream.
    :param on: Date of the withdrawal, recorded on the record.
    :returns: The IDs withdrawn in this call (already-withdrawn records are left alone).
    """
    records = read_records(path)
    done: list[str] = []
    for record in records:
        if str(record["comment_id"]) in withdrawn and record.get("withdrawn") is not True:
            record["body_text"] = None
            record["withdrawn"] = True
            record["withdrawn_on"] = on.isoformat()
            done.append(str(record["comment_id"]))
    if done:
        _replace(path, file_bytes(records))
    return done
