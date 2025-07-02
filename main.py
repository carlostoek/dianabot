import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from database_init import init_db
from handlers import onboarding, backpack, combination, vip_access
from middlewares.vip_middleware import VIPMiddleware

async def main() -> None:
    await init_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(onboarding.router)
    dp.include_router(backpack.router)
    dp.include_router(combination.router)
    dp.include_router(vip_access.router)
    # VIP middleware can be attached to specific channels if needed
    # dp.message.middleware(VIPMiddleware(channel_id=0))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
