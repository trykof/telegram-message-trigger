import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from telegram_message_trigger.config import settings
from telegram_message_trigger.handlers.common import router as common_router


async def run() -> None:
    logging.basicConfig(level=settings.log_level)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(common_router)

    await dispatcher.start_polling(
        bot,
        allowed_updates=[
            "message",
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
