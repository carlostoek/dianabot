import logging
import os
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from handlers.start_handler import StartHandler
from handlers.callback_handler import CallbackHandler
from handlers.command_handlers import CommandHandlers
from config.database import get_db, init_db

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DianaBot:
    """Bot principal de Diana - Sistema de Seducción Narrativa"""

    def __init__(self, initialize_db=True):
        self.token = self._get_token()
        
        # Inicializar base de datos condicionalmente
        if initialize_db:
            try:
                init_db()
                logger.info("✅ Base de datos inicializada")
            except Exception as e:
                logger.error(f"❌ Error inicializando BD: {e}")
                raise

        # Crear aplicación
        self.application = Application.builder().token(self.token).build()
        
        # Configurar handlers
        self._setup_handlers()

    def _get_token(self):
        """Obtiene y valida el token del bot"""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN no encontrado")
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
        
        # Validación básica del formato del token
        if not token.count(':') == 1 or len(token.split(':')[0]) < 8:
            logger.error("❌ Formato de token inválido")
            raise ValueError("Formato de token de Telegram inválido")
            
        return token

    def _setup_handlers(self):
        """Configura todos los handlers del bot"""
        try:
            # Handlers principales con validación
            start_handler = StartHandler()
            callback_handler = CallbackHandler()
            command_handlers = CommandHandlers()

            # Comandos
            self.application.add_handler(
                CommandHandler("start", start_handler.handle_start)
            )
            self.application.add_handler(
                CommandHandler("help", command_handlers.help_command)
            )
            self.application.add_handler(
                CommandHandler("profile", command_handlers.profile_command)
            )

            # Callbacks (botones)
            self.application.add_handler(
                CallbackQueryHandler(callback_handler.handle_callback)
            )

            # Handler de errores
            self.application.add_error_handler(self._error_handler)

            logger.info("✅ Handlers configurados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error configurando handlers: {e}")
            raise

    async def _error_handler(self, update, context):
        """Maneja errores elegantemente"""
        # Log detallado del error
        error_msg = (
            f"Error: {context.error}\n"
            f"Update: {update}\n"
            f"User: {update.effective_user.id if update and update.effective_user else 'Unknown'}\n"
            f"Chat: {update.effective_chat.id if update and update.effective_chat else 'Unknown'}"
        )
        logger.error(error_msg)

        # Respuesta al usuario solo si es posible
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🎭 *Lucien con disculpas*\n\n"
                    "Ha ocurrido un inconveniente técnico. "
                    "Diana me pide que te asegure que esto se resolverá pronto.\n\n"
                    "Usa /start para continuar.",
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"No se pudo enviar mensaje de error: {e}")

    def run(self):
        """Ejecuta el bot"""
        try:
            logger.info("🎭 Diana Bot iniciando...")
            logger.info("✨ Sistema de Seducción Narrativa activado")

            # Ejecutar bot
            self.application.run_polling(
                allowed_updates=["message", "callback_query"], 
                drop_pending_updates=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error ejecutando bot: {e}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        bot = DianaBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)
        
