from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.keyboards.menu import main_menu_keyboard
from telegram_message_trigger.keyboards.wizard import cancel_keyboard, whole_word_keyboard
from telegram_message_trigger.services.rules import (
    create_rule,
    find_conflicting_trigger,
    parse_trigger_input,
)
from telegram_message_trigger.states.rule_wizard import AddRuleStates
from telegram_message_trigger.texts import MAIN_MENU_TEXT

router = Router(name="add_rule")


@router.callback_query(AddRuleStates.case_sensitivity, F.data.startswith("case:"))
async def set_case_sensitivity(callback: CallbackQuery, state: FSMContext) -> None:
    case_sensitive = callback.data == "case:sensitive"
    await state.update_data(case_sensitive=case_sensitive)
    await state.set_state(AddRuleStates.whole_word)
    await edit_or_answer(
        callback,
        "Шаг 2 из 4. Триггер должен быть отдельным словом или может входить в состав других слов?",
        whole_word_keyboard(),
    )
    await callback.answer()


@router.callback_query(AddRuleStates.whole_word, F.data.startswith("word:"))
async def set_whole_word(callback: CallbackQuery, state: FSMContext) -> None:
    whole_word = callback.data == "word:whole"
    await state.update_data(whole_word=whole_word)
    await state.set_state(AddRuleStates.triggers)
    await edit_or_answer(
        callback,
        "Шаг 3 из 4. Пришлите триггеры этого правила — каждый с новой строки или через запятую.",
        cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddRuleStates.triggers, F.text)
async def set_triggers(message: Message, state: FSMContext, session: AsyncSession) -> None:
    assert message.text is not None
    triggers = parse_trigger_input(message.text)
    if not triggers:
        await message.answer("Не нашёл ни одного триггера, попробуйте ещё раз.", reply_markup=cancel_keyboard())
        return

    data = await state.get_data()
    conflict = await find_conflicting_trigger(
        session, data["owner_id"], data["case_sensitive"], data["whole_word"], triggers
    )
    if conflict is not None:
        await message.answer(
            f"Триггер «{conflict.new_trigger}» пересекается с триггером «{conflict.existing_trigger}» "
            f"в правиле #{conflict.existing_rule_id}. Измените список триггеров.",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(triggers=triggers)
    await state.set_state(AddRuleStates.reply_text)
    await message.answer(
        "Шаг 4 из 4. Что бот должен ответить при срабатывании правила?", reply_markup=cancel_keyboard()
    )


@router.message(AddRuleStates.reply_text, F.text)
async def set_reply_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    assert message.text is not None
    data = await state.get_data()
    await create_rule(
        session,
        owner_id=data["owner_id"],
        case_sensitive=data["case_sensitive"],
        whole_word=data["whole_word"],
        trigger_texts=data["triggers"],
        reply_text=message.text,
    )
    await state.clear()
    await message.answer("Правило создано и активно.")
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
