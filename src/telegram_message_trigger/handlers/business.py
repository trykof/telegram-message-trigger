from aiogram import Router
from aiogram.types import BusinessConnection, Message
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.handlers._util import message_to_html
from telegram_message_trigger.services.matching import rule_matches, scope_matches
from telegram_message_trigger.services.owners import (
    get_owner_by_business_connection,
    set_connection,
)
from telegram_message_trigger.services.rules import list_active_rules

router = Router(name="business")


@router.business_connection()
async def on_business_connection(event: BusinessConnection, session: AsyncSession) -> None:
    await set_connection(session, event.user.id, event.id, event.is_enabled)


@router.business_message()
async def on_business_message(message: Message, session: AsyncSession) -> None:
    if not message.business_connection_id:
        return

    owner = await get_owner_by_business_connection(session, message.business_connection_id)
    if owner is None or not owner.is_connected:
        return

    if not message.from_user or message.from_user.id == owner.telegram_user_id:
        return

    if not message.text and not message.caption:
        return
    text = message_to_html(message)

    rules = await list_active_rules(session, owner.id)
    for rule in rules:
        if scope_matches(rule.target_telegram_user_id, message.from_user.id) and rule_matches(text, rule):
            await message.answer(rule.reply_text)
            return
