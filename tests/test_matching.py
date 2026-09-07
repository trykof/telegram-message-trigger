from telegram_message_trigger.services.matching import trigger_matches, triggers_overlap


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
