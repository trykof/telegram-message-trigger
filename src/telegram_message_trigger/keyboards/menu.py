from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить правило", callback_data="menu:add_rule")
    builder.button(text="📋 Мои правила", callback_data="menu:list_rules")
    builder.adjust(1)
    return builder.as_markup()


def connect_check_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить подключение", callback_data="check_connection")
    return builder.as_markup()
