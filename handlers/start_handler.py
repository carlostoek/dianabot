from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from services.user_service import UserService
from typing import Dict, Any

class StartHandler:
    """Handler del comando /start - Encapsulado para MVP"""

    def __init__(self):
        self.user_service = UserService()

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /start - MVP funcional"""

        user_data = {
            "telegram_id": update.effective_user.id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
        }

        # Token VIP desactivado temporalmente para MVP
        # Original: self.channel_service.get_channel_by_token(token)
        # Conectaba con: ChannelService - pendiente de reactivación
        if context.args and len(context.args) > 0:
            if context.args[0].startswith("vip_token_"):
                await update.message.reply_text("Funcionalidad VIP desactivada temporalmente.")
                return

        # Crear o obtener usuario
        user = self.user_service.get_or_create_user(user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user.id)

        # Verificar si es usuario nuevo o recurrente
        if getattr(user, "created_today", False):
            await update.message.reply_text(f"¡Bienvenido {user.first_name}! Tu aventura comienza ahora.")
        else:
            await update.message.reply_text(f"¡Hola de nuevo {user.first_name}! Continuemos tu historia.")

# NOTA:
# Se eliminó la dependencia de ChannelService para MVP funcional.
# Se encapsuló la experiencia para solo mostrar mensajes simples sin flujo narrativo complejo.
# Los métodos pendientes o rutas incompletas fueron desactivados.
