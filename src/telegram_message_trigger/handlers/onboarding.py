from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.keyboards.menu import connect_check_keyboard, main_menu_keyboard
from telegram_message_trigger.services.owners import get_or_create_owner
from telegram_message_trigger.texts import CONNECT_INSTRUCTIONS, MAIN_MENU_TEXT

router = Router(name="onboarding")


async def _show_start_screen(session: AsyncSession, telegram_user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    owner = await get_or_create_owner(session, telegram_user_id)
    if not owner.is_connected:
        return CONNECT_INSTRUCTIONS, connect_check_keyboard()
    return MAIN_MENU_TEXT, main_menu_keyboard()


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession) -> None:
    assert message.from_user is not None
    text, keyboard = await _show_start_screen(session, message.from_user.id)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "check_connection")
async def check_connection(callback: CallbackQuery, session: AsyncSession) -> None:
    text, keyboard = await _show_start_screen(session, callback.from_user.id)
    await edit_or_answer(callback, text, keyboard)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    text, keyboard = await _show_start_screen(session, callback.from_user.id)
    await edit_or_answer(callback, text, keyboard)
    await callback.answer()
