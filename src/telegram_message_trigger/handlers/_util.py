from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.text_decorations import html_decoration


async def edit_or_answer(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    message = callback.message
    assert isinstance(message, Message)
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as error:
        if "message is not modified" not in error.message:
            raise


def message_to_html(message: Message) -> str:
    """Render a message's text/caption with its entities (incl. custom emoji) back to HTML.

    Custom emoji only survive as `<tg-emoji emoji-id="...">` markup — the plain
    .text/.caption carries just the fallback glyph, so triggers and replies must be
    captured and matched through this instead of the raw text.
    """
    if message.text is not None:
        return html_decoration.unparse(message.text, message.entities)
    if message.caption is not None:
        return html_decoration.unparse(message.caption, message.caption_entities)
    return ""
