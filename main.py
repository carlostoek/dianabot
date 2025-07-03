import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from handlers.start_handler import StartHandler
from handlers.callback_handler_narrative import CallbackHandlerNarrative
from handlers.command_handlers import CommandHandlers
from config.database import get_db, init_db

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class DianaBot:
    """Bot principal de Diana - Sistema de Seducción Narrativa"""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")

        # Inicializar base de datos
        init_db()

        # Crear aplicación
        self.application = Application.builder().token(self.token).build()

        # Configurar handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Configura todos los handlers del bot"""

        # Handlers principales
        start_handler = StartHandler()
        callback_handler = CallbackHandlerNarrative()  # 🔥 NUEVO HANDLER NARRATIVO
        command_handlers = CommandHandlers()

        # Comandos
        self.application.add_handler(
            CommandHandler("start", start_handler.handle_start)  # ✅ CORREGIDO
        )
        self.application.add_handler(
            CommandHandler("help", command_handlers.help_command)
        )
        self.application.add_handler(
            CommandHandler("profile", command_handlers.profile_command)
        )

        # Callbacks (botones) - 🔥 AHORA CON NARRATIVA
        self.application.add_handler(
            CallbackQueryHandler(callback_handler.handle_callback)
        )

        # Handler de errores
        self.application.add_error_handler(self._error_handler)

        logger.info("✅ Handlers configurados correctamente")

    async def _error_handler(self, update, context):
        """Maneja errores elegantemente"""

        logger.error(f"Error: {context.error}")

        if update and update.effective_message:
            await update.effective_message.reply_text(
                "🎭 *Lucien con disculpas*\n\n"
                "Ha ocurrido un inconveniente técnico. "
                "Diana me pide que te asegure que esto se resolverá pronto.\n\n"
                "Usa /start para continuar.",
                parse_mode="Markdown",
            )

    def run(self):
        """Ejecuta el bot"""
        logger.info("🎭 Diana Bot iniciando...")
        logger.info("✨ Sistema de Seducción Narrativa activado")

        # Ejecutar bot
        self.application.run_polling(
            allowed_updates=["message", "callback_query"], drop_pending_updates=True
        )


if __name__ == "__main__":
    bot = DianaBot()
    bot.run()
    
