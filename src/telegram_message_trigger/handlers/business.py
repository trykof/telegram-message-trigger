from aiogram import Router
from aiogram.types import BusinessConnection, Message
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.services.matching import rule_matches
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

    if message.from_user and message.from_user.id == owner.telegram_user_id:
        return

    text = message.text or message.caption
    if not text:
        return

    rules = await list_active_rules(session, owner.id)
    for rule in rules:
        if rule_matches(text, rule):
            await message.answer(rule.reply_text)
            return
