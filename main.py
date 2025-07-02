import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from database_init import init_db
from handlers import onboarding, backpack


def setup_bot() -> Dispatcher:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(onboarding.router)
    dp.include_router(backpack.router)
    return bot, dp

async def main():
    bot, dp = setup_bot()
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
