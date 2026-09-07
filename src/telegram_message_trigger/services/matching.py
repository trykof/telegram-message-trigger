import re
from typing import NamedTuple

from telegram_message_trigger.db.models import Rule


class TriggerConflict(NamedTuple):
    new_trigger: str
    existing_trigger: str
    existing_rule_id: int


def trigger_matches(message_text: str, trigger_text: str, case_sensitive: bool, whole_word: bool) -> bool:
    haystack = message_text if case_sensitive else message_text.lower()
    needle = trigger_text if case_sensitive else trigger_text.lower()
    if not needle:
        return False
    if whole_word:
        pattern = rf"(?<!\w){re.escape(needle)}(?!\w)"
        return re.search(pattern, haystack) is not None
    return needle in haystack


def rule_matches(message_text: str, rule: Rule) -> bool:
    return any(
        trigger_matches(message_text, trigger.text, rule.case_sensitive, rule.whole_word)
        for trigger in rule.triggers
    )


def scope_matches(target_telegram_user_id: int | None, message_from_user_id: int) -> bool:
    return target_telegram_user_id is None or target_telegram_user_id == message_from_user_id


def scopes_can_overlap(target_a: int | None, target_b: int | None) -> bool:
    return target_a is None or target_b is None or target_a == target_b


def triggers_overlap(
    text_a: str,
    case_sensitive_a: bool,
    whole_word_a: bool,
    text_b: str,
    case_sensitive_b: bool,
    whole_word_b: bool,
) -> bool:
    fold = not (case_sensitive_a and case_sensitive_b)
    a = text_a.lower() if fold else text_a
    b = text_b.lower() if fold else text_b
    if not a or not b:
        return False
    if whole_word_a and whole_word_b:
        return a == b
    return a in b or b in a
