from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.keyboards.menu import main_menu_keyboard
from telegram_message_trigger.keyboards.rules import rules_list_keyboard
from telegram_message_trigger.keyboards.wizard import case_sensitivity_keyboard
from telegram_message_trigger.services.owners import get_or_create_owner
from telegram_message_trigger.services.rules import list_rules
from telegram_message_trigger.states.rule_wizard import AddRuleStates

router = Router(name="menu")


@router.callback_query(F.data == "menu:add_rule")
async def add_rule_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    owner = await get_or_create_owner(session, callback.from_user.id)
    await state.set_state(AddRuleStates.case_sensitivity)
    await state.update_data(owner_id=owner.id)
    await edit_or_answer(callback, "Шаг 1 из 4. Учитывать регистр триггеров?", case_sensitivity_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:list_rules")
async def show_rules_list(callback: CallbackQuery, session: AsyncSession) -> None:
    owner = await get_or_create_owner(session, callback.from_user.id)
    rules = await list_rules(session, owner.id)
    if not rules:
        await edit_or_answer(callback, "У вас пока нет правил.", main_menu_keyboard())
    else:
        await edit_or_answer(callback, "Ваши правила:", rules_list_keyboard(rules))
    await callback.answer()
