from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_answer(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    message = callback.message
    assert isinstance(message, Message)
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as error:
        if "message is not modified" not in error.message:
            raise
