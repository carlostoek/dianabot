import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import Settings
from config.database import init_db
from middlewares.auth import AuthMiddleware
from middlewares.logging import LoggingMiddleware
from middlewares.analytics import AnalyticsMiddleware
from middlewares.economy import EconomyMiddleware

from handlers.start_handler import StartHandler
from handlers.user_handlers import UserHandlers
from handlers.narrative_handlers import NarrativeHandlers
from handlers.store_handlers import StoreHandlers
from handlers.auction_handlers import AuctionHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.channel_handlers import ChannelHandlers
from handlers.cms_handlers import CMSHandlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DianaBot:
    def __init__(self):
        self.settings = Settings()
        self.bot = Bot(
            token=self.settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.dp = Dispatcher(storage=MemoryStorage())
        self._setup_middlewares()
        self._setup_handlers()

    def _setup_middlewares(self):
        """Configurar middlewares"""
        self.dp.message.middleware(AuthMiddleware())
        self.dp.callback_query.middleware(AuthMiddleware())
        self.dp.message.middleware(LoggingMiddleware())
        self.dp.callback_query.middleware(LoggingMiddleware())
        self.dp.message.middleware(AnalyticsMiddleware())
        self.dp.callback_query.middleware(AnalyticsMiddleware())
        self.dp.message.middleware(EconomyMiddleware())
        self.dp.callback_query.middleware(EconomyMiddleware())

    def _setup_handlers(self):
        """Configurar handlers"""
        handlers = [
            StartHandler(),
            UserHandlers(),
            NarrativeHandlers(),
            StoreHandlers(),
            AuctionHandlers(),
            AdminHandlers(),
            ChannelHandlers(),
            CMSHandlers()
        ]
        
        for handler in handlers:
            handler.register(self.dp)

    async def start(self):
        """Iniciar el bot"""
        await init_db()
        logger.info("🎭 DianaBot 2.0 iniciando...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """Detener el bot"""
        await self.bot.session.close()

async def main():
    bot = DianaBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
  
