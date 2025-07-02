import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from database_init import init_db
from handlers import onboarding, backpack, combination, vip_access, notifications
from middlewares.vip_middleware import VIPMiddleware
from middlewares.logging import LoggingMiddleware
from utils.notification_scheduler import NotificationScheduler

async def main() -> None:
    await init_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.message.middleware(LoggingMiddleware())
    dp.include_router(onboarding.router)
    dp.include_router(backpack.router)
    dp.include_router(combination.router)
    dp.include_router(vip_access.router)
    dp.include_router(notifications.router)
    # VIP middleware can be attached to specific channels if needed
    # dp.message.middleware(VIPMiddleware(channel_id=0))
    scheduler = NotificationScheduler(bot)
    await scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
