import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from database_init import init_db
from handlers import onboarding, backpack

async def main() -> None:
    await init_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(onboarding.router)
    dp.include_router(backpack.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
