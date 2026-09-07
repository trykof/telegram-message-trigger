from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.keyboards.menu import main_menu_keyboard
from telegram_message_trigger.texts import MAIN_MENU_TEXT

router = Router(name="wizard_common")


@router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_or_answer(callback, MAIN_MENU_TEXT, main_menu_keyboard())
    await callback.answer("Отменено")
