from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.handlers.rules_list import show_rules_list_view
from telegram_message_trigger.keyboards.wizard import case_sensitivity_keyboard
from telegram_message_trigger.services.owners import get_or_create_owner
from telegram_message_trigger.states.rule_wizard import AddRuleStates

router = Router(name="menu")


@router.callback_query(F.data == "menu:add_rule")
async def add_rule_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    owner = await get_or_create_owner(session, callback.from_user.id)
    await state.set_state(AddRuleStates.case_sensitivity)
    await state.update_data(owner_id=owner.id)
    await edit_or_answer(callback, "Шаг 1 из 5. Учитывать регистр триггеров?", case_sensitivity_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:list_rules")
async def show_rules_list(callback: CallbackQuery, session: AsyncSession) -> None:
    owner = await get_or_create_owner(session, callback.from_user.id)
    await show_rules_list_view(callback, session, owner.id)
    await callback.answer()
