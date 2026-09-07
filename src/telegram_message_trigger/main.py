import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from telegram_message_trigger.config import settings
from telegram_message_trigger.db.session import async_session_factory
from telegram_message_trigger.handlers.add_rule import router as add_rule_router
from telegram_message_trigger.handlers.business import router as business_router
from telegram_message_trigger.handlers.menu import router as menu_router
from telegram_message_trigger.handlers.onboarding import router as onboarding_router
from telegram_message_trigger.handlers.rules_list import router as rules_list_router
from telegram_message_trigger.handlers.wizard_common import router as wizard_common_router
from telegram_message_trigger.middlewares.db import DbSessionMiddleware


async def run() -> None:
    logging.basicConfig(level=settings.log_level)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(DbSessionMiddleware(async_session_factory))

    dispatcher.include_router(onboarding_router)
    dispatcher.include_router(menu_router)
    dispatcher.include_router(add_rule_router)
    dispatcher.include_router(rules_list_router)
    dispatcher.include_router(wizard_common_router)
    dispatcher.include_router(business_router)

    await dispatcher.start_polling(
        bot,
        allowed_updates=[
            "message",
            "callback_query",
            "business_connection",
            "business_message",
            "edited_business_message",
            "deleted_business_messages",
        ],
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
