import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from handlers.start_handler import StartHandler
from handlers.callback_handler_narrative import CallbackHandlerNarrative
from handlers.command_handlers import CommandHandlers
from config.database import get_db, init_db
from services.channel_service import ChannelService
from services.user_service import UserService

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_new_channel_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-responde cuando un usuario se une a un canal."""
    channel_service = ChannelService()
    user_service = UserService()

    if not update.message or not update.message.new_chat_members:
        return

    new_member = update.message.new_chat_members[0]
    user_data = {
        "telegram_id": new_member.id,
        "username": new_member.username,
        "first_name": new_member.first_name,
        "last_name": new_member.last_name,
    }

    user = user_service.get_or_create_user(user_data)
    channel_id = update.effective_chat.id

    response = channel_service.handle_join_request(channel_id, user.id, new_member.id)
    if "auto_message" in response:
        await context.bot.send_message(chat_id=channel_id, text=response["auto_message"])


async def generate_vip_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando para generar tokens VIP temporales."""
    channel_service = ChannelService()
    admin_user_id = update.effective_user.id
    channel_id = update.effective_chat.id

    token_info = channel_service.generate_vip_access_token(
        channel_id,
        admin_user_id,
        {
            "expiry_hours": 24,
            "max_uses": 1,
            "description": "Token VIP para acceso temporal",
        },
    )

    if "token" in token_info:
        message = (
            f"Token VIP generado: {token_info['token']}\n"
            f"Enlace: {token_info.get('invite_link', 'N/A')}"
        )
        await context.bot.send_message(chat_id=channel_id, text=message)

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
        self.application.add_handler(
            CommandHandler("create_first_admin", command_handlers.create_first_admin_command)
        )
        self.application.add_handler(
            CommandHandler("admin_panel", command_handlers.handle_admin_panel)
        )
        self.application.add_handler(
            CommandHandler("generate_vip_token", generate_vip_token)
        )
        self.application.add_handler(
            MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_channel_member
            )
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
    
