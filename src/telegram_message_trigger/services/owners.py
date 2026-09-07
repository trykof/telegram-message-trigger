from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_message_trigger.db.models import Owner


async def get_or_create_owner(session: AsyncSession, telegram_user_id: int) -> Owner:
    result = await session.execute(select(Owner).where(Owner.telegram_user_id == telegram_user_id))
    owner = result.scalar_one_or_none()
    if owner is None:
        owner = Owner(telegram_user_id=telegram_user_id)
        session.add(owner)
        await session.commit()
        await session.refresh(owner)
    return owner


async def get_owner_by_business_connection(session: AsyncSession, business_connection_id: str) -> Owner | None:
    result = await session.execute(
        select(Owner).where(Owner.business_connection_id == business_connection_id)
    )
    return result.scalar_one_or_none()


async def set_connection(
    session: AsyncSession, telegram_user_id: int, business_connection_id: str, is_enabled: bool
) -> Owner:
    owner = await get_or_create_owner(session, telegram_user_id)
    owner.business_connection_id = business_connection_id
    owner.is_connected = is_enabled
    await session.commit()
    return owner
