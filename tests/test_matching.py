from telegram_message_trigger.services.matching import (
    scope_matches,
    scopes_can_overlap,
    trigger_matches,
    triggers_overlap,
)


def test_case_insensitive_substring_matches_regardless_of_case() -> None:
    assert trigger_matches("Привет, КОТ!", "кот", case_sensitive=False, whole_word=False)


def test_case_sensitive_requires_exact_case() -> None:
    assert not trigger_matches("привет, кот!", "КОТ", case_sensitive=True, whole_word=False)
    assert trigger_matches("привет, КОТ!", "КОТ", case_sensitive=True, whole_word=False)


def test_substring_mode_matches_inside_other_words() -> None:
    assert trigger_matches("котенок", "кот", case_sensitive=False, whole_word=False)


def test_whole_word_mode_rejects_substring_inside_other_word() -> None:
    assert not trigger_matches("котенок", "кот", case_sensitive=False, whole_word=True)
    assert trigger_matches("сидит кот", "кот", case_sensitive=False, whole_word=True)


def test_overlap_exact_duplicate_case_insensitive() -> None:
    assert triggers_overlap("кот", False, True, "КОТ", False, True)


def test_no_overlap_different_case_when_both_case_sensitive() -> None:
    assert not triggers_overlap("кот", True, True, "КОТ", True, True)


def test_overlap_substring_containment() -> None:
    assert triggers_overlap("кот", False, False, "котенок", False, False)


def test_no_overlap_unrelated_whole_word_triggers() -> None:
    assert not triggers_overlap("кот", False, True, "собака", False, True)


def test_scope_all_chats_matches_anyone() -> None:
    assert scope_matches(None, 111)


def test_scope_specific_contact_matches_only_that_id() -> None:
    assert scope_matches(111, 111)
    assert not scope_matches(111, 222)


def test_scopes_can_overlap_when_either_is_all_chats() -> None:
    assert scopes_can_overlap(None, None)
    assert scopes_can_overlap(None, 111)
    assert scopes_can_overlap(111, None)


def test_scopes_cannot_overlap_for_different_specific_contacts() -> None:
    assert scopes_can_overlap(111, 111)
    assert not scopes_can_overlap(111, 222)
