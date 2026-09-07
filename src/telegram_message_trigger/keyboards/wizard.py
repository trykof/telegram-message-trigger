from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def case_sensitivity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Учитывать регистр", callback_data="case:sensitive")
    builder.button(text="Не учитывать регистр", callback_data="case:insensitive")
    builder.button(text="❌ Отмена", callback_data="wizard:cancel")
    builder.adjust(1)
    return builder.as_markup()


def whole_word_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Только отдельным словом", callback_data="word:whole")
    builder.button(text="Может быть частью другого слова", callback_data="word:substring")
    builder.button(text="❌ Отмена", callback_data="wizard:cancel")
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="wizard:cancel")
    return builder.as_markup()
