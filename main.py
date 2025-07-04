import asyncio
import logging
import sys
import os

# Configurar logging básico primero
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Función principal del bot"""
    try:
        logger.info("🚀 Iniciando DianaBot 2.0...")
        
        # Verificar BOT_TOKEN primero
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("❌ BOT_TOKEN no encontrado en variables de entorno")
            logger.info("💡 Asegúrate de configurar: export BOT_TOKEN=tu_token_aqui")
            return
        
        logger.info("✅ BOT_TOKEN encontrado")
        
        # Importar después de verificar token
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
                logger.error("❌ No se pudo inicializar la base de datos")
                return
        except Exception as e:
            logger.error(f"❌ Error en configuración de base de datos: {e}")
            return
        
        # Crear bot y dispatcher
        logger.info("🤖 Creando bot...")
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        dp = Dispatcher(storage=MemoryStorage())
        
        # Configurar handlers básicos
        logger.info("📡 Configurando handlers...")
        try:
            from handlers.start_handler import StartHandler
            
            # Solo cargar handler básico por ahora
            start_handler = StartHandler()
            start_handler.register(dp)
            
            logger.info("✅ Handler básico configurado")
            
            # Intentar cargar handlers adicionales
            try:
                from handlers.user_handlers import UserHandlers
                from handlers.narrative_handlers import NarrativeHandlers
                
                user_handler = UserHandlers()
                narrative_handler = NarrativeHandlers()
                
                user_handler.register(dp)
                narrative_handler.register(dp)
                
                logger.info("✅ Handlers adicionales configurados")
            except Exception as e:
                logger.warning(f"⚠️ Algunos handlers no se cargaron: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando handlers: {e}")
            return
        
        # Configurar middlewares (opcional)
        try:
            from middlewares.auth import AuthMiddleware
            dp.message.middleware(AuthMiddleware())
            dp.callback_query.middleware(AuthMiddleware())
            logger.info("✅ Middlewares configurados")
        except Exception as e:
            logger.warning(f"⚠️ Middlewares no se pudieron cargar: {e}")
        
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
    # Verificar Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requerido")
        sys.exit(1)
    
    # Ejecutar bot
    asyncio.run(main())
    
