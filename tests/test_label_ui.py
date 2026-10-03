"""The browser labeling interface: same records as the terminal tool, local only, safe page."""

from __future__ import annotations

import http.client
import json
import re
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, label_ui, labeling, service
from afterword.label_ui_page import PAGE
from afterword.observations import ObservedComment, ObservedContent, RunObservations
from tests.test_labeling import NAMES, Script, label_answers, lines, make_run, ticker

T0 = datetime(2026, 8, 1, tzinfo=UTC)


def many_posts(posts: int = 6, per_post: int = 3) -> labeling.Snapshot:
    contents = [
        ObservedContent(f"p{i}", T0 + timedelta(days=i), per_post, title=f"Synthetic post {i}")
        for i in range(posts)
    ]
    comments = [
        ObservedComment(
            content_ref=f"p{i}",
            source_object_id=f"c{i}_{j}",
            parent_source_object_id=None,
            depth=0,
            # Later comments first in source order, to prove time order is applied.
            created_at=T0 + timedelta(days=i, hours=per_post - j),
            is_content_author=False,
            author_ref=f"u{j}",
            body_source=f"<p>Synthetic comment {i} {j}</p>",
            body_source_format="HTML",
        )
        for i in range(posts)
        for j in range(per_post)
    ]
    return labeling.Snapshot(RunObservations("syn", "all", T0, contents, comments))


def post_runs(order: list[ObservedComment]) -> list[str]:
    runs: list[str] = []
    for c in order:
        if not runs or runs[-1] != c.content_ref:
            runs.append(c.content_ref)
    return runs


# Post order --------------------------------------------------------------------


def test_random_post_order_is_seeded_and_keeps_posts_whole_and_oldest_first():
    snap = many_posts()
    published = snap.subjects()
    shuffled = snap.subjects(post_order="random", seed=7)

    assert post_runs(published) == [f"p{i}" for i in range(6)]
    assert sorted(c.source_object_id for c in shuffled) == sorted(
        c.source_object_id for c in published
    )
    assert len(post_runs(shuffled)) == 6  # each post appears as one contiguous run
    for ref in post_runs(shuffled):
        times = [c.created_at for c in shuffled if c.content_ref == ref]
        assert times == sorted(times)
    assert snap.subjects(post_order="random", seed=7) == shuffled
    orders = {tuple(post_runs(snap.subjects(post_order="random", seed=s))) for s in range(10)}
    assert len(orders) > 1


def test_random_post_order_needs_a_seed_and_known_orders_only():
    snap = many_posts()
    with pytest.raises(ValueError):
        snap.subjects(post_order="random")
    with pytest.raises(ValueError):
        snap.subjects(post_order="alphabetical", seed=1)


def test_resumed_random_batches_continue_the_same_order(tmp_path):
    snap = many_posts()
    expected = [c.source_object_id for c in snap.subjects(post_order="random", seed=3)]
    seen: list[str] = []
    for _ in range(3):
        batch = labeling.LabelBatch(snap, root=tmp_path, batch_size=6, post_order="random", seed=3)
        batch.start()
        for i, c in enumerate(batch.items):
            seen.append(c.source_object_id)
            batch.save(record(batch, i))
        batch.end("complete")
    assert seen == expected
    starts = [e for e in batch_events(tmp_path) if e["event"] == "batch_start"]
    assert {(e["post_order"], e["seed"]) for e in starts} == {("random", 3)}


def test_cli_label_refuses_random_order_without_a_seed(tmp_path, fake_dev, capsys):
    make_run(tmp_path)
    base = ["--root", str(tmp_path), "label", "--run", "r1", "--posts", "random"]
    assert cli.main(base) == 2
    assert "--posts random needs --seed" in capsys.readouterr().err


def test_cli_label_records_the_seed(tmp_path, fake_dev, monkeypatch):
    make_run(tmp_path)
    answers = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    args = ["--root", str(tmp_path), "label", "--run", "r1", "--posts", "random", "--seed", "11"]
    assert cli.main(args) == 0
    (start, _end) = batch_events(tmp_path)
    assert start["post_order"] == "random"
    assert start["seed"] == 11


# Controller ---------------------------------------------------------------------


def record(batch: labeling.LabelBatch, index: int) -> dict[str, Any]:
    return labeling.make_label(
        batch.snap,
        batch.items[index],
        batch.context(),
        primary="CONVERSATIONAL",
        flags=[],
        prospective=0,
        retrospective=None,
        reason="",
        duration_seconds=1.0,
        labeled_at=T0,
    )


def batch_events(root: Path) -> list[dict[str, Any]]:
    return lines(root / labeling.LABEL_ROOT / "unfrozen" / "batches.jsonl")


def opened(root: Path) -> service.LabelingSession:
    make_run(root)
    return service.open_for_labeling(root, "r1")


def make_ui(root: Path, **options: Any) -> label_ui.LabelUI:
    ui = label_ui.LabelUI(
        session=opened(root),
        root=root,
        options=label_ui.BatchOptions(**options),
        monotonic=ticker(2.5).__next__,
    )
    ui.start_batch()
    return ui


def answer(ui: label_ui.LabelUI, **fields: Any) -> dict[str, Any]:
    state = ui.state()
    body = {
        "comment_id": state["comment"]["comment_id"],
        "primary_class": "TECHNICAL_QUESTION",
        "flags": ["REFERENCES_SPECIFIC_CLAIM"],
        "prospective": 2,
        "retrospective": 3,
        "reason": "needs an answer",
        "note": "",
    }
    return body | fields


def test_the_ui_writes_the_same_label_as_the_terminal(tmp_path, fake_dev):
    terminal_root, ui_root = tmp_path / "terminal", tmp_path / "ui"
    make_run(terminal_root)
    session = service.open_for_labeling(terminal_root, "r1")
    script = Script([*label_answers(), "q"])
    service.label_batch(
        session,
        script.console,
        root=terminal_root,
        pass_name="initial",
        corpus_version="unfrozen",
        corpus_set="dev",
        batch_size=40,
        only_ids=None,
    )
    (from_terminal,) = lines(terminal_root / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")

    ui = make_ui(ui_root)
    ui.submit(answer(ui))
    (from_ui,) = lines(ui_root / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")

    varying = {"batch_id", "duration_seconds", "labeled_at"}
    assert {k: v for k, v in from_ui.items() if k not in varying} == {
        k: v for k, v in from_terminal.items() if k not in varying
    }
    assert list(from_ui) == list(from_terminal)
    assert from_ui["sample_kind"] == "researcher"
    assert from_ui["duration_seconds"] == 2.5


def test_state_shows_as_of_context_with_pseudonyms_only(tmp_path, fake_dev):
    ui = make_ui(tmp_path)
    for _ in range(2):
        ui.submit(answer(ui, prospective=0, reason=""))
    state = ui.state()
    comment = state["comment"]
    assert comment["comment_id"] == "s1a3"
    assert comment["reply_to_author"] is True
    assert [t["who"] for t in comment["thread"]] == ["Commenter A", "You (author)", "Commenter A"]
    assert comment["thread"][-1]["is_this"] is True
    text = json.dumps(state)
    for name in NAMES:
        assert name not in text
    assert {c["key"] for c in state["taxonomy"]["classes"]} == set("0123456789")


def test_invalid_labels_are_refused_and_nothing_is_written(tmp_path, fake_dev):
    ui = make_ui(tmp_path)
    labels = tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl"
    bad = [
        {"primary_class": None},
        {"primary_class": "NOT_A_CLASS"},
        {"flags": ["REPLY_TO_AUTHOR"]},
        {"flags": "CONTAINS_CODE"},
        {"prospective": None},
        {"prospective": True},
        {"prospective": 4},
        {"retrospective": "3"},
        {"prospective": 3, "reason": "   "},
        {"comment_id": "s1b1"},
    ]
    for fields in bad:
        with pytest.raises(label_ui.RequestError):
            ui.submit(answer(ui, **fields))
    assert not labels.exists()
    assert ui.state()["position"] == 1


def test_skip_note_completion_and_next_batch(tmp_path, fake_dev):
    ui = make_ui(tmp_path, batch_size=2)
    ui.skip({"comment_id": "s1a1", "note": "ambiguous"})
    ui.submit(answer(ui, note="second thoughts"))
    state = ui.state()
    assert state["status"] == "batch_done"
    assert (state["labeled"], state["skipped"]) == (1, 1)
    events = batch_events(tmp_path)
    assert [e["event"] for e in events] == ["batch_start", "note", "note", "batch_end"]
    assert events[-1]["ended_by"] == "complete"
    labels = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert all("note" not in label for label in labels)

    ui.next_batch()
    assert ui.state()["comment"]["comment_id"] == "s1a1"  # skipped, so still unlabeled
    ui.stop()
    assert batch_events(tmp_path)[-1]["ended_by"] == "quit"
    assert ui.state()["status"] == "stopped"


def test_next_batch_is_refused_mid_batch_and_nothing_left_is_reported(tmp_path, fake_dev):
    ui = make_ui(tmp_path)
    with pytest.raises(label_ui.RequestError):
        ui.next_batch()
    while ui.state()["status"] == "labeling":
        ui.submit(answer(ui, prospective=1, reason=""))
    ui.next_batch()
    assert ui.state()["status"] == "nothing_left"


# HTTP -----------------------------------------------------------------------------


class Running:
    def __init__(self, root: Path) -> None:
        self.ui = make_ui(root)
        self.server = label_ui.create_server(self.ui, port=0)
        self.port = self.server.httpd.server_address[1]
        self.thread = threading.Thread(target=self.server.serve, daemon=True)
        self.thread.start()

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        token: str | None = None,
        host: str | None = None,
        content_type: str = "application/json",
    ) -> tuple[int, Any]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        if token is not None:
            headers["X-Afterword-Token"] = token
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = content_type
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        conn.close()
        kind = response.getheader("Content-Type", "")
        return response.status, json.loads(raw) if "json" in kind else raw.decode()

    def close(self) -> None:
        if self.thread.is_alive():
            self.server.httpd.shutdown()
        self.thread.join(timeout=10)


@pytest.fixture
def running(tmp_path, fake_dev):
    r = Running(tmp_path)
    yield r
    r.close()


def test_server_binds_to_loopback_only(running):
    assert running.server.httpd.server_address[0] == "127.0.0.1"
    assert running.server.url.startswith(f"http://127.0.0.1:{running.port}/?t=")


def test_every_request_needs_the_token_and_the_local_host(running):
    token = running.server.token
    assert running.request("GET", "/")[0] == 403
    assert running.request("GET", "/?t=wrong")[0] == 403
    status, page = running.request("GET", f"/?t={token}")
    assert status == 200
    assert token in page and "__TOKEN__" not in page
    assert running.request("GET", "/api/state")[0] == 403
    assert running.request("GET", "/api/state", token=token, host="evil.example:80")[0] == 403
    assert running.request("GET", f"/?t={token}", host=f"evil.example:{running.port}")[0] == 403
    status, state = running.request("GET", "/api/state", token=token)
    assert status == 200 and state["status"] == "labeling"


def test_writes_need_json_and_the_token(running):
    token = running.server.token
    body = answer(running.ui)
    assert running.request("POST", "/api/label", body)[0] == 403
    assert (
        running.request("POST", "/api/label", body, token=token, content_type="text/plain")[0]
        == 415
    )
    assert running.request("POST", "/api/nope", {}, token=token)[0] == 404
    status, refused = running.request("POST", "/api/label", body | {"prospective": 9}, token=token)
    assert status == 409 and "0 to 3" in refused["error"]


def test_a_label_round_trip_and_stop_over_http(running, tmp_path):
    token = running.server.token
    status, state = running.request("POST", "/api/label", answer(running.ui), token=token)
    assert status == 200 and state["position"] == 2
    (label,) = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert label["comment_id"] == "s1a1"

    status, state = running.request("POST", "/api/stop", {}, token=token)
    assert status == 200 and state["status"] == "stopped"
    running.thread.join(timeout=10)
    assert not running.thread.is_alive()
    assert batch_events(tmp_path)[-1]["ended_by"] == "quit"


def test_cli_label_ui_prints_counts_and_the_url_only(tmp_path, fake_dev, capsys, monkeypatch):
    make_run(tmp_path)
    opened_urls: list[str] = []
    monkeypatch.setattr(label_ui.Server, "serve", lambda self: self.ui.stop())
    monkeypatch.setattr("webbrowser.open", opened_urls.append)
    args = ["--root", str(tmp_path), "label-ui", "--run", "r1", "--port", "0"]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "4 comments to label" in out
    assert "open: http://127.0.0.1:" in out
    assert len(opened_urls) == 1
    for name in NAMES:
        assert name not in out
    assert "Synthetic question" not in out


def test_cli_label_ui_validates_like_label(tmp_path, fake_dev, capsys):
    make_run(tmp_path)
    base = ["--root", str(tmp_path), "label-ui", "--run", "r1", "--no-browser"]
    assert cli.main([*base, "--batch-size", "41"]) == 2
    assert cli.main([*base, "--posts", "random"]) == 2
    assert cli.main([*base, "--corpus-version", "../x"]) == 2


# The page ---------------------------------------------------------------------------


def test_the_page_is_self_contained_and_inserts_text_safely():
    assert PAGE.isascii()
    assert not re.search(r"https?://", PAGE)
    assert not re.search(r"<(?:link|img|iframe)\b|\bsrc\s*=|@import|url\(", PAGE)
    assert "innerHTML" not in PAGE and "outerHTML" not in PAGE
    assert "insertAdjacentHTML" not in PAGE and "eval(" not in PAGE
    assert "textContent" in PAGE


def test_keys_are_distinct_and_cover_every_class_and_labeler_flag():
    assert len(label_ui.CLASS_KEYS) == len(labeling.CLASSES)
    assert set(label_ui.FLAG_KEYS) == set(labeling.LABELER_FLAGS)
    flag_keys = list(label_ui.FLAG_KEYS.values())
    assert len(set(flag_keys)) == len(flag_keys)
    assert not set(flag_keys) & label_ui.COMMAND_KEYS
    assert not set(flag_keys) & set(label_ui.CLASS_KEYS)


def test_the_workflow_shortcut_table_matches_the_keys():
    workflow = (Path(__file__).resolve().parents[1] / "docs" / "WORKFLOW.md").read_text(
        encoding="utf-8"
    )
    for flag, key in label_ui.FLAG_KEYS.items():
        assert f"| `{key}` | `{flag}` |" in workflow
    assert "| `1` to `9`, `0` |" in workflow
    assert labeling.CLASSES[-1] == "UNCERTAIN"  # documented as the `0` key


def test_batches_started_in_the_same_second_get_distinct_ids(tmp_path):
    snap = many_posts()
    ids = []
    for _ in range(3):
        batch = labeling.LabelBatch(snap, root=tmp_path, batch_size=2, now=lambda: T0)
        ids.append(batch.start().batch_id)
        batch.end("quit")
    assert ids == ["b_20260801T000000Z", "b_20260801T000000Z_2", "b_20260801T000000Z_3"]
