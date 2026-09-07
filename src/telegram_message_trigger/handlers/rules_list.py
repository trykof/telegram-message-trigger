from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.db.models import Rule
from telegram_message_trigger.handlers._util import edit_or_answer, message_to_html
from telegram_message_trigger.keyboards.rules import rule_detail_keyboard
from telegram_message_trigger.keyboards.wizard import (
    cancel_keyboard,
    case_sensitivity_keyboard,
    contact_request_keyboard,
    scope_keyboard,
    whole_word_keyboard,
)
from telegram_message_trigger.services.rules import (
    find_conflict_for_rule,
    find_conflicting_trigger,
    format_target_label,
    get_rule,
    parse_trigger_input,
    set_rule_active,
    update_rule_matching,
    update_rule_reply,
    update_rule_scope,
    update_rule_triggers,
)
from telegram_message_trigger.states.rule_wizard import (
    EditMatchingStates,
    EditReplyStates,
    EditScopeStates,
    EditTriggersStates,
)
from telegram_message_trigger.text_format import strip_html_preview

router = Router(name="rules_list")


def _extract_rule_id(callback: CallbackQuery) -> int:
    assert callback.data is not None
    return int(callback.data.split(":")[1])


def _render_rule_detail(rule: Rule) -> str:
    status = "включено" if rule.is_active else "отключено"
    case = "учитывается" if rule.case_sensitive else "не учитывается"
    word = "только отдельным словом" if rule.whole_word else "может быть частью другого слова"
    triggers = "\n".join(f"• {t.text}" for t in rule.triggers)
    scope = rule.target_label if rule.target_telegram_user_id is not None else "все чаты"
    return (
        f"Правило #{rule.id} ({status})\n\n"
        f"Регистр: {case}\n"
        f"Совпадение: {word}\n"
        f"Чат: {scope}\n\n"
        f"Триггеры:\n{triggers}\n\n"
        f"Ответ:\n{rule.reply_text}"
    )


async def _show_rule_detail(callback: CallbackQuery, session: AsyncSession, rule_id: int) -> None:
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return
    await edit_or_answer(callback, _render_rule_detail(rule), rule_detail_keyboard(rule))


@router.callback_query(F.data.regexp(r"^rule:(\d+)$"))
async def show_rule_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_rule_detail(callback, session, _extract_rule_id(callback))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):toggle$"))
async def toggle_rule(callback: CallbackQuery, session: AsyncSession) -> None:
    rule_id = _extract_rule_id(callback)
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return

    if rule.is_active:
        await set_rule_active(session, rule, False)
    else:
        conflict = await find_conflict_for_rule(session, rule)
        if conflict is not None:
            await callback.answer(
                f"Нельзя включить: триггер «{strip_html_preview(conflict.new_trigger)}» пересекается с "
                f"«{strip_html_preview(conflict.existing_trigger)}» в правиле #{conflict.existing_rule_id}.",
                show_alert=True,
            )
            return
        await set_rule_active(session, rule, True)

    await _show_rule_detail(callback, session, rule_id)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):edit_matching$"))
async def edit_matching_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    rule_id = _extract_rule_id(callback)
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return
    await state.set_state(EditMatchingStates.case_sensitivity)
    await state.update_data(rule_id=rule_id)
    await edit_or_answer(callback, "Шаг 1 из 2. Учитывать регистр триггеров?", case_sensitivity_keyboard())
    await callback.answer()


@router.callback_query(EditMatchingStates.case_sensitivity, F.data.startswith("case:"))
async def edit_set_case_sensitivity(callback: CallbackQuery, state: FSMContext) -> None:
    case_sensitive = callback.data == "case:sensitive"
    await state.update_data(case_sensitive=case_sensitive)
    await state.set_state(EditMatchingStates.whole_word)
    await edit_or_answer(
        callback,
        "Шаг 2 из 2. Триггер должен быть отдельным словом или может входить в состав других слов?",
        whole_word_keyboard(),
    )
    await callback.answer()


@router.callback_query(EditMatchingStates.whole_word, F.data.startswith("word:"))
async def edit_set_whole_word(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    whole_word = callback.data == "word:whole"
    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    if rule is None:
        await state.clear()
        await callback.answer("Правило не найдено", show_alert=True)
        return

    conflict = await find_conflicting_trigger(
        session,
        rule.owner_id,
        data["case_sensitive"],
        whole_word,
        [t.text for t in rule.triggers],
        target_telegram_user_id=rule.target_telegram_user_id,
        exclude_rule_id=rule.id,
    )
    if conflict is not None:
        await state.clear()
        await callback.answer(
            f"С такими условиями триггер «{strip_html_preview(conflict.new_trigger)}» пересечётся с "
            f"«{strip_html_preview(conflict.existing_trigger)}» в правиле #{conflict.existing_rule_id}. "
            "Изменения не сохранены.",
            show_alert=True,
        )
        await _show_rule_detail(callback, session, rule.id)
        return

    await update_rule_matching(session, rule, data["case_sensitive"], whole_word)
    await state.clear()
    await _show_rule_detail(callback, session, rule.id)
    await callback.answer("Сохранено")


@router.callback_query(F.data.regexp(r"^rule:(\d+):edit_triggers$"))
async def edit_triggers_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    rule_id = _extract_rule_id(callback)
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return
    await state.set_state(EditTriggersStates.triggers)
    await state.update_data(rule_id=rule_id)
    current = "\n".join(f"• {t.text}" for t in rule.triggers)
    await edit_or_answer(
        callback,
        f"Текущие триггеры:\n{current}\n\n"
        "Пришлите новый список триггеров — каждый с новой строки или через запятую. "
        "Он полностью заменит текущий.",
        cancel_keyboard(),
    )
    await callback.answer()


@router.message(EditTriggersStates.triggers, F.text)
async def edit_set_triggers(message: Message, state: FSMContext, session: AsyncSession) -> None:
    triggers = parse_trigger_input(message_to_html(message))
    if not triggers:
        await message.answer("Не нашёл ни одного триггера, попробуйте ещё раз.", reply_markup=cancel_keyboard())
        return

    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    if rule is None:
        await state.clear()
        await message.answer("Правило не найдено.")
        return

    conflict = await find_conflicting_trigger(
        session,
        rule.owner_id,
        rule.case_sensitive,
        rule.whole_word,
        triggers,
        target_telegram_user_id=rule.target_telegram_user_id,
        exclude_rule_id=rule.id,
    )
    if conflict is not None:
        await message.answer(
            f"Триггер «{strip_html_preview(conflict.new_trigger)}» пересекается с триггером "
            f"«{strip_html_preview(conflict.existing_trigger)}» в правиле #{conflict.existing_rule_id}. "
            "Измените список триггеров.",
            reply_markup=cancel_keyboard(),
        )
        return

    await update_rule_triggers(session, rule, triggers)
    await state.clear()
    await message.answer(_render_rule_detail(rule), reply_markup=rule_detail_keyboard(rule))


@router.callback_query(F.data.regexp(r"^rule:(\d+):edit_reply$"))
async def edit_reply_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    rule_id = _extract_rule_id(callback)
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return
    await state.set_state(EditReplyStates.reply_text)
    await state.update_data(rule_id=rule_id)
    await edit_or_answer(
        callback, f"Текущий ответ:\n{rule.reply_text}\n\nПришлите новый текст ответа.", cancel_keyboard()
    )
    await callback.answer()


@router.message(EditReplyStates.reply_text, F.text)
async def edit_set_reply(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    if rule is None:
        await state.clear()
        await message.answer("Правило не найдено.")
        return

    await update_rule_reply(session, rule, message_to_html(message))
    await state.clear()
    await message.answer(_render_rule_detail(rule), reply_markup=rule_detail_keyboard(rule))


@router.callback_query(F.data.regexp(r"^rule:(\d+):edit_scope$"))
async def edit_scope_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    rule_id = _extract_rule_id(callback)
    rule = await get_rule(session, rule_id)
    if rule is None:
        await callback.answer("Правило не найдено", show_alert=True)
        return
    await state.set_state(EditScopeStates.scope)
    await state.update_data(rule_id=rule_id)
    await edit_or_answer(callback, "В каком чате должно работать правило?", scope_keyboard())
    await callback.answer()


@router.callback_query(EditScopeStates.scope, F.data == "scope:all")
async def edit_set_scope_all(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    if rule is None:
        await state.clear()
        await callback.answer("Правило не найдено", show_alert=True)
        return

    conflict = await find_conflicting_trigger(
        session,
        rule.owner_id,
        rule.case_sensitive,
        rule.whole_word,
        [t.text for t in rule.triggers],
        target_telegram_user_id=None,
        exclude_rule_id=rule.id,
    )
    if conflict is not None:
        await state.clear()
        await callback.answer(
            f"Нельзя: триггер «{strip_html_preview(conflict.new_trigger)}» пересечётся с "
            f"«{strip_html_preview(conflict.existing_trigger)}» в правиле #{conflict.existing_rule_id}. "
            "Изменения не сохранены.",
            show_alert=True,
        )
        await _show_rule_detail(callback, session, rule.id)
        return

    await update_rule_scope(session, rule, None, None)
    await state.clear()
    await _show_rule_detail(callback, session, rule.id)
    await callback.answer("Сохранено")


@router.callback_query(EditScopeStates.scope, F.data == "scope:contact")
async def edit_set_scope_contact(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EditScopeStates.scope_contact)
    await edit_or_answer(callback, "Выберите контакт кнопкой ниже.", None)
    message = callback.message
    assert isinstance(message, Message)
    await message.answer("Нажмите кнопку, чтобы выбрать контакт:", reply_markup=contact_request_keyboard())
    await callback.answer()


@router.message(EditScopeStates.scope_contact, F.users_shared)
async def edit_set_scope_contact_picked(message: Message, state: FSMContext, session: AsyncSession) -> None:
    assert message.users_shared is not None
    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    if rule is None:
        await state.clear()
        await message.answer("Правило не найдено.", reply_markup=ReplyKeyboardRemove())
        return

    shared = message.users_shared.users[0]
    label = format_target_label(shared.user_id, shared.first_name, shared.last_name, shared.username)
    conflict = await find_conflicting_trigger(
        session,
        rule.owner_id,
        rule.case_sensitive,
        rule.whole_word,
        [t.text for t in rule.triggers],
        target_telegram_user_id=shared.user_id,
        exclude_rule_id=rule.id,
    )
    await message.answer("Контакт выбран.", reply_markup=ReplyKeyboardRemove())
    if conflict is not None:
        await state.clear()
        await message.answer(
            f"Нельзя: триггер «{strip_html_preview(conflict.new_trigger)}» пересечётся с "
            f"«{strip_html_preview(conflict.existing_trigger)}» в правиле #{conflict.existing_rule_id}. "
            "Изменения не сохранены."
        )
        await message.answer(_render_rule_detail(rule), reply_markup=rule_detail_keyboard(rule))
        return

    await update_rule_scope(session, rule, shared.user_id, label)
    await state.clear()
    await message.answer(_render_rule_detail(rule), reply_markup=rule_detail_keyboard(rule))


@router.message(EditScopeStates.scope_contact, F.text == "❌ Отмена")
async def edit_cancel_scope_contact(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    rule = await get_rule(session, data["rule_id"])
    await state.clear()
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
    if rule is not None:
        await message.answer(_render_rule_detail(rule), reply_markup=rule_detail_keyboard(rule))
