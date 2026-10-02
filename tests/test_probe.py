from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

from afterword import cli
from afterword.adapters.dev.client import DevClient
from afterword.adapters.dev.probe import FINDINGS_FILE, INDEX_FILE, Probe
from tests.conftest import FAKE_KEY

COMMENT_TEXT_AND_NAMES = (
    "Synthetic question",
    "Synthetic reply",
    "Synthetic follow-up",
    "Synthetic acknowledgment",
    "synthetic_reader_1",
    "Synthetic Reader One",
    "synthetic_reader_2",
)


def run_probe(tmp_path: Path, run_id: str, **kwargs) -> dict:
    client = DevClient(FAKE_KEY, min_interval=0.0, sleep=lambda s: None)
    probe = Probe(
        client, tmp_path / "raw" / run_id, tmp_path / "reports" / run_id, run_id=run_id, page_size=2
    )
    return probe.run(**kwargs)


def all_text(root: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file())


def test_full_probe_records_capability_evidence(tmp_path, fake_dev):
    f = run_probe(tmp_path, "r1")

    assert f["outcome"] == "COMPLETE", f["limitations"]
    assert f["auth"]["me_status"] == 200
    assert f["auth"]["invalid_key_status"] == 401
    assert f["auth"]["unauthenticated_comments_status"] == 200
    assert f["auth"]["unauthenticated_matches_authenticated"] is True

    articles = f["articles"]
    assert articles["items_per_page"] == [2, 1, 0]
    assert articles["terminates_on_empty_page"] is True
    assert articles["total_via_small_pages"] == 3
    assert articles["id_sets_equal"] is True
    assert articles["duplicates_across_pages"] == 0

    comments = f["comments"]
    assert comments["total_nodes"] == 5
    assert comments["by_content_author"] == 1
    assert comments["max_depth"] == 2
    assert comments["id_code"]["present"] == 5
    assert comments["created_at"]["parse_with_timezone"] == 5
    assert comments["edit_key_candidates"] == []
    assert comments["parent_key_candidates"] == []
    assert comments["count_reconciliation"]["mismatches"] == []

    assert f["largest_thread"] == {"article_id": 9000001, "nodes": 4}
    assert f["comment_pagination"]["params_ignored"] is False
    assert f["comment_pagination"]["nodes_with_params"] == 1  # second top-level thread
    assert f["single_comment_fetch"]["matches_tree_subtree"] is True
    assert f["article_fetch"]["content_item_fields_present"]["published_at"] is True
    assert f["rate_limits"]["rate_limit_headers_seen"] == {"x-ratelimit-remaining": ["29"]}


def test_probe_writes_raw_to_raw_dir_and_safe_outputs_to_reports(tmp_path, fake_dev):
    run_probe(tmp_path, "r1")
    raw = tmp_path / "raw" / "r1"
    reports = tmp_path / "reports" / "r1"
    assert (raw / "run.json").exists()
    assert (raw / "comments-a9000001.json").exists()
    assert {p.name for p in reports.iterdir()} == {FINDINGS_FILE, "shapes.json", INDEX_FILE}
    # Real payloads stay in raw/; nothing readable for review carries text or names.
    report_text = all_text(reports)
    for value in COMMENT_TEXT_AND_NAMES:
        assert value not in report_text


def test_key_never_written_printed_or_logged(tmp_path, fake_dev, monkeypatch, capsys, caplog):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    monkeypatch.setattr("time.sleep", lambda s: None)
    caplog.set_level(logging.DEBUG)
    assert cli.main(["--root", str(tmp_path), "probe", "--min-interval", "0"]) == 0
    (run_dir,) = (tmp_path / cli.RAW_ROOT).iterdir()
    assert cli.main(["--root", str(tmp_path), "baseline", "--run", run_dir.name]) == 0
    assert not (tmp_path / cli.REPORT_ROOT / "probe" / cli.LOCK_FILE).exists()

    captured = capsys.readouterr()
    assert FAKE_KEY not in all_text(tmp_path)
    assert FAKE_KEY not in captured.out + captured.err
    assert FAKE_KEY not in caplog.text
    for value in COMMENT_TEXT_AND_NAMES:
        assert value not in captured.out + captured.err


def test_missing_key_exits_cleanly(tmp_path, capsys):
    assert cli.main(["--root", str(tmp_path), "probe"]) == 2
    assert "DEV_API_KEY is not set" in capsys.readouterr().err


def test_failed_auth_stops_early(tmp_path, fake_dev):
    client = DevClient("wrong-key", min_interval=0.0, sleep=lambda s: None)
    f = Probe(client, tmp_path / "raw", tmp_path / "rep", run_id="x").run()
    assert f["outcome"] == "FAILED"
    assert f["auth"]["me_status"] == 401
    assert len(fake_dev.calls) == 1


def test_lifecycle_detects_deletion_and_placeholder(tmp_path, fake_dev):
    run_probe(tmp_path, "r1", article=9000001)

    # Case 1: a leaf comment disappears. Case 2: a comment with a reply becomes a placeholder.
    thread = fake_dev.comments[9000001]
    thread.pop()  # s1b1, no children
    thread[0]["body_html"] = "<p>[deleted]</p>"
    f = run_probe(tmp_path, "r2", article=9000001, compare_to=tmp_path / "reports" / "r1")

    life = f["lifecycle"]
    assert life["compared_to"] == "r1"
    assert life["removed"] == [{"id_code": "s1b1", "had_children": 0}]
    assert life["added"] == []
    (changed,) = life["changed"]
    assert changed["id_code"] == "s1a1"
    assert changed["values_changed"] == ["body_html"]
    assert changed["placeholder_like"] == [False, True]
    assert changed["children_after"] == 1
    assert life["unchanged"] == 2
    # Scoped runs skip the account-wide checks.
    assert "articles" not in f
    assert f["scope"] == "article:9000001"
    assert json.loads((tmp_path / "raw" / "r2" / "run.json").read_text())["article_ids"] == [
        9000001
    ]


def test_article_url_resolves_to_id(tmp_path, fake_dev):
    url = "https://dev.to/synthetic_author/synthetic-article-two-efgh"
    f = run_probe(tmp_path, "r1", article=url)
    assert f["outcome"] == "COMPLETE", f["limitations"]
    assert f["scope"] == "article:9000002"
    assert f["comments"]["total_nodes"] == 1


def test_unresolvable_article_fails_cleanly(tmp_path, fake_dev):
    f = run_probe(tmp_path, "r1", article="https://dev.to/nobody/missing")
    assert f["outcome"] == "FAILED"
    assert f["limitations"] == ["article path lookup returned 404"]


def test_account_payload_is_reduced_to_user_id_before_saving(tmp_path, fake_dev):
    f = run_probe(tmp_path, "r1")
    saved = json.loads((tmp_path / "raw" / "r1" / "users-me.json").read_text())
    assert saved["response"]["body"] == {"id": 1001}
    assert "email" in f["redacted_before_save"]
    assert "author@example.invalid" not in all_text(tmp_path)
    # The shape (key names and types only) is still recorded as evidence.
    shapes = json.loads((tmp_path / "reports" / "r1" / "shapes.json").read_text())
    assert "$.email" in shapes["users_me"]["paths"]
    assert f["comments"]["by_content_author"] == 1  # author matching needs only the ID


def test_ai_disclosure_distribution(tmp_path, fake_dev):
    f = run_probe(tmp_path, "r1")
    label = f["comments"]["ai_disclosure"]["ai_disclosure_label"]
    assert label["all"] == {"<absent>": 3, "synthetic_val": 2}
    assert label["from_others"] == {"<absent>": 2, "synthetic_val": 2}


def test_second_probe_is_refused_while_one_holds_the_lock(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    lock = tmp_path / cli.REPORT_ROOT / "probe" / cli.LOCK_FILE
    lock.parent.mkdir(parents=True)
    lock.write_text("{}")
    assert cli.main(["--root", str(tmp_path), "probe"]) == 3
    assert "another probe is running" in capsys.readouterr().err
    assert lock.exists()  # someone else's lock is left alone


def test_baseline_refuses_scoped_runs(tmp_path, fake_dev, monkeypatch, capsys):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    args = ["--root", str(tmp_path), "probe", "--min-interval", "0", "--article", "9000001"]
    assert cli.main(args) == 0
    (run_dir,) = (tmp_path / cli.RAW_ROOT).iterdir()
    assert cli.main(["--root", str(tmp_path), "baseline", "--run", run_dir.name]) == 2
    assert "needs a full-scope run" in capsys.readouterr().err


def test_digit_only_id_codes_stay_strings(tmp_path, fake_dev):
    run_probe(tmp_path, "r1")
    index = json.loads((tmp_path / "reports" / "r1" / INDEX_FILE).read_text())
    assert "4821" in [c["id_code"] for c in index["comments"]]


def test_cache_headers_are_summarized_per_endpoint_and_auth(tmp_path, fake_dev):
    f = run_probe(tmp_path, "r1")
    cache = f["http_cache_by_endpoint"]
    assert cache["/api/comments [auth=key]"]["cache-control"] == ["public, max-age=0"]
    assert "/api/comments [auth=none]" in cache


def test_retries_are_logged_with_server_error_body(tmp_path, no_live_api):
    no_live_api.get("https://dev.to/api/users/me").mock(
        side_effect=[
            httpx.Response(
                429, json={"error": "slow down", "status": 429}, headers={"retry-after": "1"}
            ),
            httpx.Response(401, json={"error": "unauthorized", "status": 401}),
        ]
    )
    f = run_probe(tmp_path, "r1")
    (retry,) = f["rate_limits"]["retries"]
    assert retry["endpoint"] == "/api/users/me [auth=key]"
    assert retry["retry_after"] == "1"
    assert retry["body"] == {"error": "slow down", "status": 429}


def test_deletion_placeholder_reconciles_and_shows_in_lifecycle(tmp_path, fake_dev):
    run_probe(tmp_path, "r1", article=9000001)
    # DEV behavior from the hand test: the parent with a reply becomes a placeholder
    # (body replaced, user emptied) and comments_count stops counting it.
    parent = fake_dev.comments[9000001][0]
    parent.update(body_html="<p>[deleted]</p>", user={})
    fake_dev.articles[0]["comments_count"] = 3
    f = run_probe(tmp_path, "r2", article=9000001, compare_to=tmp_path / "reports" / "r1")

    assert f["comments"]["deletion_observation"]["deletion_placeholders"] == 1
    assert f["comments"]["count_reconciliation"]["mismatches"] == []
    assert f["comments"]["by_content_author"] == 1
    (changed,) = f["lifecycle"]["changed"]
    assert changed["values_changed"] == ["body_html", "user"]
