from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="common")


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Бот запущен и на связи.")
