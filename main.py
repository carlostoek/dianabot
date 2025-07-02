import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from database_init import init_db
from handlers import onboarding, backpack, combination, vip_access
from middlewares.vip_middleware import VIPMiddleware


def setup_bot() -> Dispatcher:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(onboarding.router)
    dp.include_router(backpack.router)
    dp.include_router(combination.router)
    dp.include_router(vip_access.router)
    dp.message.middleware(VIPMiddleware(channel_id=0))
    return bot, dp

async def main():
    bot, dp = setup_bot()
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
