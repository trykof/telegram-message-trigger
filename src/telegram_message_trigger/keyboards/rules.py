from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_message_trigger.db.models import Rule


def _rule_label(rule: Rule) -> str:
    status = "🟢" if rule.is_active else "🔴"
    preview = rule.triggers[0].text if rule.triggers else "…"
    if len(rule.triggers) > 1:
        preview += f" +{len(rule.triggers) - 1}"
    return f"{status} {preview}"


def rules_list_keyboard(rules: list[Rule]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for rule in rules:
        builder.button(text=_rule_label(rule), callback_data=f"rule:{rule.id}")
    builder.button(text="⬅️ В меню", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def rule_detail_keyboard(rule: Rule) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔤 Изменить условия совпадения", callback_data=f"rule:{rule.id}:edit_matching")
    builder.button(text="✏️ Изменить триггеры", callback_data=f"rule:{rule.id}:edit_triggers")
    builder.button(text="💬 Изменить ответ", callback_data=f"rule:{rule.id}:edit_reply")
    builder.button(text="🎯 Изменить чат", callback_data=f"rule:{rule.id}:edit_scope")
    toggle_text = "🔴 Отключить" if rule.is_active else "🟢 Включить"
    builder.button(text=toggle_text, callback_data=f"rule:{rule.id}:toggle")
    builder.button(text="⬅️ К списку", callback_data="menu:list_rules")
    builder.adjust(1)
    return builder.as_markup()
