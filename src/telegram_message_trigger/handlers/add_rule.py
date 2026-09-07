from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import edit_or_answer
from telegram_message_trigger.keyboards.menu import main_menu_keyboard
from telegram_message_trigger.keyboards.wizard import (
    cancel_keyboard,
    contact_request_keyboard,
    scope_keyboard,
    whole_word_keyboard,
)
from telegram_message_trigger.services.rules import (
    create_rule,
    find_conflicting_trigger,
    format_target_label,
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
        "Шаг 2 из 5. Триггер должен быть отдельным словом или может входить в состав других слов?",
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
        "Шаг 3 из 5. Пришлите триггеры этого правила — каждый с новой строки или через запятую.",
        cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddRuleStates.triggers, F.text)
async def set_triggers(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    triggers = parse_trigger_input(message.text)
    if not triggers:
        await message.answer("Не нашёл ни одного триггера, попробуйте ещё раз.", reply_markup=cancel_keyboard())
        return

    await state.update_data(triggers=triggers)
    await state.set_state(AddRuleStates.reply_text)
    await message.answer(
        "Шаг 4 из 5. Что бот должен ответить при срабатывании правила?", reply_markup=cancel_keyboard()
    )


@router.message(AddRuleStates.reply_text, F.text)
async def set_reply_text(message: Message, state: FSMContext) -> None:
    assert message.text is not None
    await state.update_data(reply_text=message.text)
    await state.set_state(AddRuleStates.scope)
    await message.answer("Шаг 5 из 5. В каком чате должно работать правило?", reply_markup=scope_keyboard())


async def _finalize_rule(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    target_telegram_user_id: int | None,
    target_label: str | None,
) -> None:
    data = await state.get_data()
    conflict = await find_conflicting_trigger(
        session,
        data["owner_id"],
        data["case_sensitive"],
        data["whole_word"],
        data["triggers"],
        target_telegram_user_id=target_telegram_user_id,
    )
    if conflict is not None:
        await state.set_state(AddRuleStates.triggers)
        text = (
            f"Триггер «{conflict.new_trigger}» пересекается с триггером «{conflict.existing_trigger}» "
            f"в правиле #{conflict.existing_rule_id}. Пришлите список триггеров ещё раз."
        )
        if isinstance(message_or_callback, CallbackQuery):
            await edit_or_answer(message_or_callback, text, cancel_keyboard())
        else:
            await message_or_callback.answer(text, reply_markup=cancel_keyboard())
        return

    await create_rule(
        session,
        owner_id=data["owner_id"],
        case_sensitive=data["case_sensitive"],
        whole_word=data["whole_word"],
        trigger_texts=data["triggers"],
        reply_text=data["reply_text"],
        target_telegram_user_id=target_telegram_user_id,
        target_label=target_label,
    )
    await state.clear()
    bot_message = (
        message_or_callback.message if isinstance(message_or_callback, CallbackQuery) else message_or_callback
    )
    assert isinstance(bot_message, Message)
    await bot_message.answer("Правило создано и активно.")
    await bot_message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(AddRuleStates.scope, F.data == "scope:all")
async def set_scope_all(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await _finalize_rule(callback, state, session, target_telegram_user_id=None, target_label=None)
    await callback.answer()


@router.callback_query(AddRuleStates.scope, F.data == "scope:contact")
async def set_scope_contact(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddRuleStates.scope_contact)
    await edit_or_answer(callback, "Выберите контакт кнопкой ниже.", None)
    message = callback.message
    assert isinstance(message, Message)
    await message.answer("Нажмите кнопку, чтобы выбрать контакт:", reply_markup=contact_request_keyboard())
    await callback.answer()


@router.message(AddRuleStates.scope_contact, F.users_shared)
async def set_scope_contact_picked(message: Message, state: FSMContext, session: AsyncSession) -> None:
    assert message.users_shared is not None
    shared = message.users_shared.users[0]
    label = format_target_label(shared.user_id, shared.first_name, shared.last_name, shared.username)
    await message.answer("Контакт выбран.", reply_markup=ReplyKeyboardRemove())
    await _finalize_rule(message, state, session, target_telegram_user_id=shared.user_id, target_label=label)


@router.message(AddRuleStates.scope_contact, F.text == "❌ Отмена")
async def cancel_scope_contact(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
    await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
