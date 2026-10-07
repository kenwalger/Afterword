from __future__ import annotations

from afterword.adapters.dev import records
from tests.conftest import load


def test_flatten_assigns_depth_and_derived_parent():
    nodes = records.flatten_comments(load("comments-by-article.json"))
    assert [(n.id_code, n.parent_id_code, n.depth) for n in nodes] == [
        ("s1a1", None, 0),
        ("s1a2", "s1a1", 1),
        ("s1a3", "s1a2", 2),
        ("s1b1", None, 0),
    ]


def test_flatten_accepts_single_comment_object():
    nodes = records.flatten_comments(load("comment-with-descendants.json"))
    assert [n.id_code for n in nodes] == ["s1a1", "s1a2", "s1a3"]


def test_content_author_matches_by_user_id_then_username():
    me = records.identity_from_me(load("users-me.json"))
    nodes = records.flatten_comments(load("comments-by-article.json"))
    assert [records.is_by(me, n.node) for n in nodes] == [False, True, False, False]

    by_name = records.AuthorIdentity(user_id=None, username="synthetic_author")
    assert records.is_by(by_name, nodes[1].node)
    assert not records.is_by(me, {"user": None})


def test_parse_timestamp_requires_timezone():
    assert records.parse_timestamp("2026-08-03T14:00:00Z") is not None
    assert records.parse_timestamp("2026-08-03T14:00:00") is None
    assert records.parse_timestamp(None) is None


def test_key_candidates():
    keys = {"id_code", "created_at", "edited_at", "updated_at", "parent_id", "children"}
    assert records.edit_key_candidates(keys) == ["edited_at", "updated_at"]
    assert records.parent_key_candidates(keys) == ["parent_id"]


def test_enum_distribution_never_echoes_free_text():
    nodes = [
        {"k": "ai_assisted"},
        {"k": None},
        {},
        {"k": "This looks like a sentence, with punctuation."},
        {"k": 3},
    ]
    assert records.enum_distribution(nodes, "k") == {
        "<absent>": 1,
        "<non-enum value>": 2,
        "<null>": 1,
        "ai_assisted": 1,
    }


def test_deletion_placeholder_is_detected_structurally():
    parent, reply = records.flatten_comments(load("comments-with-deletion-placeholder.json"))
    assert records.is_deletion_placeholder(parent.node)
    assert not records.is_deletion_placeholder(reply.node)
    assert reply.parent_id_code == parent.id_code  # the reply keeps its thread position
    assert not records.is_deletion_placeholder({"user": None})
    assert not records.is_unexpected_shape(parent.node)
    assert not records.is_unexpected_shape(reply.node)


def test_other_authorless_shapes_are_unexpected_not_placeholders():
    (parent, _) = records.flatten_comments(load("comments-with-deletion-placeholder.json"))
    variants = [
        {**parent.node, "user": None},  # null user
        {k: v for k, v in parent.node.items() if k != "user"},  # missing user
        {**parent.node, "deleted": True},  # extra key
        {**parent.node, "user": {"name": "x"}},  # user without user_id
    ]
    for node in variants:
        assert not records.is_deletion_placeholder(node)
        assert records.is_unexpected_shape(node)


def test_placeholder_matching_ignores_allowlisted_platform_wide_keys():
    (parent, _) = records.flatten_comments(load("comments-with-deletion-placeholder.json"))
    with_disclosure = {
        **parent.node,
        "ai_disclosure_label": "Not Disclosed",
        "ai_disclosure_level": "not_disclosed",
    }
    assert records.is_deletion_placeholder(with_disclosure)
    assert not records.is_unexpected_shape(with_disclosure)


def test_placeholder_with_an_unknown_key_is_still_unexpected():
    (parent, _) = records.flatten_comments(load("comments-with-deletion-placeholder.json"))
    for extra in ({"ai_disclosure_label": "x", "new_platform_field": 1}, {"deleted_at": "x"}):
        node = {**parent.node, **extra}
        assert not records.is_deletion_placeholder(node)
        assert records.is_unexpected_shape(node)


def test_an_authorless_node_without_the_placeholder_body_is_unexpected():
    (parent, _) = records.flatten_comments(load("comments-with-deletion-placeholder.json"))
    node = {**parent.node, "body_html": "<p>A full synthetic comment body, not a placeholder.</p>"}
    assert not records.is_deletion_placeholder(node)
    assert records.is_unexpected_shape(node)
    missing = {k: v for k, v in parent.node.items() if k != "created_at"}
    assert not records.is_deletion_placeholder(missing)
    assert records.is_unexpected_shape(missing)


def test_placeholder_like_is_a_short_body_heuristic():
    assert records.placeholder_like({"body_html": "<p>[deleted]</p>"})
    assert not records.placeholder_like({"body_html": "<p>A normal comment.</p>"})
    assert not records.placeholder_like({})


def test_field_hashes_exclude_children_and_detect_change():
    node = {"id_code": "a", "body_html": "<p>x</p>", "children": [{"id_code": "b"}]}
    before = records.field_hashes(node)
    after = records.field_hashes({**node, "body_html": "<p>y</p>", "children": []})
    assert "children" not in before
    assert before["id_code"] == after["id_code"]
    assert before["body_html"] != after["body_html"]
