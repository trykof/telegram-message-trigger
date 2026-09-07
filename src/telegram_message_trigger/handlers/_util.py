from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def edit_or_answer(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    message = callback.message
    assert isinstance(message, Message)
    await message.edit_text(text, reply_markup=keyboard)
