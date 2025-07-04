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
            if not db_success:
                logger.warning("⚠️ Base de datos no se inicializó correctamente, continuando...")
        except Exception as e:
            logger.warning(f"⚠️ Error en base de datos: {e}, continuando sin BD...")
        
        # Crear bot
        logger.info("🤖 Creando bot...")
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        dp = Dispatcher(storage=MemoryStorage())
        
        # Configurar handlers
        logger.info("📡 Configurando handlers...")
        from handlers.start_handler import StartHandler
        
        start_handler = StartHandler()
        start_handler.register(dp)
        
        logger.info("✅ Handlers configurados")
        
        # Iniciar bot
        logger.info("🎭 DianaBot 2.0 iniciado correctamente")
        logger.info("📱 El bot está listo para recibir mensajes")
        
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("🔚 Cerrando DianaBot...")

if __name__ == "__main__":
    asyncio.run(main())
    
