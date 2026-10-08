"""Dev-set analysis: tier causes, pre-check, confusion, and language counts (synthetic only)."""

from __future__ import annotations

import json

import pytest

from afterword import cli, language, precheck, service
from tests.fake_models import QWEN, FakeOllama, answer
from tests.test_evaluation import LABELS, REASON, write_labels
from tests.test_store import Runs

IDS = ("s1a1", "s1b1", "s1a3", "4821")


@pytest.fixture
def labeled(tmp_path, fake_dev):
    runs = Runs(tmp_path, fake_dev)
    runs.ingest()
    write_labels(tmp_path, LABELS)
    return runs


def classified(tmp_path, no_live_api, cls="CONVERSATIONAL", flags=()):
    fake = FakeOllama(no_live_api, reply=lambda body: answer(cls, list(flags)))
    service.classify_comments(tmp_path, condition="b1", heuristic_version="hb-v0.2")
    service.classify_comments(tmp_path, condition="b2", model=QWEN)
    return fake


def test_tier_causes_cover_every_comment_and_need_no_model(labeled, tmp_path, no_live_api):
    fake = classified(tmp_path, no_live_api, flags=["REFERENCES_SPECIFIC_CLAIM"])
    calls = len(fake.chats)
    result = service.analyze_dev(tmp_path, model=QWEN)
    assert len(fake.chats) == calls
    assert result.labels == 4
    for name in ("b1", "b2"):
        cond = result.conditions[name]
        assert cond["classified"] == result.subjects and cond["not_classified"] == 0
        for pv in ("pp-v0.1", "pp-v0.2"):
            causes = cond[pv]
            assert sum(causes["rule_applied"]["all"].values()) == result.subjects
            assert sum(causes["rule_applied"]["labeled"].values()) == 4
            assert sum(causes["by_tier"]["labeled"].values()) == 4
    b2 = result.conditions["b2"]
    # Under pp-v0.1 the model's RSC decides QUEUE wherever nothing else raises; pp-v0.2 ignores it.
    assert "override:references_specific_claim" not in b2["pp-v0.2"]["rule_applied"]["all"]
    assert b2["pp-v0.2"]["rule_applied"]["all"].get("class_default:CONVERSATIONAL", 0) > 0
    # Every labeled comment was predicted CONVERSATIONAL: one confusion row.
    assert list(result.confusion) == ["CONVERSATIONAL"]
    assert sum(result.confusion["CONVERSATIONAL"].values()) == 4


def test_precheck_counts_and_raises_alone(labeled, tmp_path, no_live_api, monkeypatch):
    real = precheck.precheck
    monkeypatch.setattr(
        precheck,
        "precheck",
        lambda text: precheck.PrecheckResult(True, ("taxonomy_name",)) if text else real(text),
    )
    classified(tmp_path, no_live_api, cls="LIGHTWEIGHT_ACKNOWLEDGMENT")
    result = service.analyze_dev(tmp_path, model=QWEN)
    pre = result.precheck
    assert pre["fired"] == pre["of"] == result.subjects
    assert pre["rules_matched"] == {"taxonomy_name": result.subjects}
    assert pre["labeled"] == 4 and pre["labeled_consequential"] == 3
    causes = result.conditions["b2"]["pp-v0.1"]
    assert causes["rule_applied"]["all"] == {"override:possible_instruction_text": result.subjects}
    # An acknowledgment would collapse, or queue on REPLY_TO_AUTHOR: the pre-check alone raised it.
    raised = causes["raised_to_surface_by_precheck_alone"]
    assert raised["all"] == result.subjects and raised["labeled_consequential"] == 3


def test_language_groups_partition_the_comments(labeled, tmp_path, no_live_api, monkeypatch):
    classified(tmp_path, no_live_api)
    codes = iter(["fr", language.TOO_SHORT, language.UNCERTAIN] + ["en"] * 100)
    monkeypatch.setattr(language, "detect", lambda prose: language.LanguageGuess(next(codes), 1.0))
    result = service.analyze_dev(tmp_path, model=QWEN)
    lang = result.language
    assert sum(lang["by_language"].values()) == result.subjects
    assert lang["by_language"]["fr"] == 1 and lang["non_english"]["comments"] == 1
    assert lang["min_chars"] == language.MIN_CHARS
    assert lang["non_english"]["model_outcomes"] == {"OK": 1}


def test_report_and_output_hold_counts_only(labeled, tmp_path, no_live_api, capsys):
    classified(tmp_path, no_live_api)
    assert cli.main(["--root", str(tmp_path), "dev-analysis", "--model", QWEN]) == 0
    out = capsys.readouterr().out
    assert "pre-check pc-v0.1 fired on" in out and REASON not in out
    (path,) = (tmp_path / service.EVAL_ROOT).glob("*-dev-analysis-*.json")
    text = path.read_text(encoding="utf-8")
    assert REASON not in text and not any(f'"{i}"' in text for i in IDS)
    assert json.loads(text)["precheck"]["version"] == "pc-v0.1"


def test_unknown_heuristic_is_refused(labeled, tmp_path):
    with pytest.raises(service.ServiceError):
        service.analyze_dev(tmp_path, model=QWEN, heuristic_version="hb-v9")


# Language detection ------------------------------------------------------------------


def test_short_text_is_not_assigned_a_language():
    assert language.detect("Thanks, works for me!") == language.LanguageGuess(
        language.TOO_SHORT, None
    )


def test_detection_is_deterministic_and_local():
    text = "This synthetic sentence talks about caching layers and database indexes."
    first = language.detect(text)
    assert first == language.detect(text) and first.language == "en"
    french = language.detect(
        "Cette phrase synthétique parle de cache et d'index de bases de données."
    )
    assert french.language == "fr"


def test_low_confidence_is_uncertain(monkeypatch):
    class Low:
        def classify(self, text):
            return "es", 0.5

    monkeypatch.setattr(language, "_identifier", lambda: Low())
    guess = language.detect("x" * language.MIN_CHARS)
    assert guess == language.LanguageGuess(language.UNCERTAIN, 0.5)
