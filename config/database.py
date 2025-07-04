import asyncio
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    """Función principal del bot"""
    try:
        logger.info("🚀 Iniciando DianaBot 2.0...")
        
        # Verificar BOT_TOKEN
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("❌ BOT_TOKEN no encontrado")
            return
        
        logger.info("✅ BOT_TOKEN encontrado")
        
        # Importar dependencias
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # Inicializar base de datos
        logger.info("🗄️ Inicializando base de datos...")
        try:
            from config.database import init_db
            db_success = await init_db()
            if db_success:
                logger.info("✅ Base de datos lista")
            else:
                logger.warning("⚠️ Base de datos con problemas, continuando...")
        except Exception as e:
            logger.warning(f"⚠️ Error en base de datos: {e}")
        
        # Crear bot
        logger.info("🤖 Creando bot...")
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        dp = Dispatcher(storage=MemoryStorage())
        
        # Configurar handlers
        logger.info("📡 Configurando handlers...")
        from handlers.start_handler import Start
