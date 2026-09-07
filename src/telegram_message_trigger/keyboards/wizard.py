from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

CONTACT_REQUEST_ID = 1


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


def scope_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Все чаты", callback_data="scope:all")
    builder.button(text="👤 Определённый контакт", callback_data="scope:contact")
    builder.button(text="❌ Отмена", callback_data="wizard:cancel")
    builder.adjust(1)
    return builder.as_markup()


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👤 Выбрать контакт",
                    request_users=KeyboardButtonRequestUsers(
                        request_id=CONTACT_REQUEST_ID,
                        user_is_bot=False,
                        max_quantity=1,
                        request_name=True,
                        request_username=True,
                    ),
                )
            ],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
