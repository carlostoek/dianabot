from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from services.user_service import UserService
from utils.lucien_voice import LucienVoice
from typing import Dict, Any


class CommandHandlers:
    """Comandos principales del bot"""

    def __init__(self):
        self.user_service = UserService()
        self.lucien = LucienVoice()

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /help elegante"""

        help_message = f"""
{self.lucien.EMOJIS['lucien']} **Guía de Interacción**

*[Con profesionalidad]*

Estos son los comandos principales para interactuar conmigo:

**🎭 Comandos Básicos:**
/start - Iniciar o regresar al menú principal
/profile - Ver tu evaluación personal
/mission - Tus misiones activas
/games - Juegos de personalidad
/help - Esta guía

**💎 Comandos Avanzados:**
/shop - Tienda exclusiva de Diana
/auction - Subastas de contenido premium
/stats - Estadísticas detalladas

{self.lucien.EMOJIS['diana']} *[Diana desde las sombras]*

"*La verdadera interacción sucede a través de los botones, {update.effective_user.first_name}. Úsalos.*"

*[Con elegancia]*

Lucien siempre está aquí para guiarte en tu camino hacia... conocer mejor a Diana.
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🎭 Menú Principal", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            help_message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def profile_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /profile directo"""

        user_data = {
            "telegram_id": update.effective_user.id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
        }

        user = self.user_service.get_or_create_user(user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user["id"])
        user_stats = self.user_service.get_user_detailed_stats(user["id"])

        quick_profile = f"""
{self.lucien.EMOJIS['lucien']} **Evaluación Rápida**

*[Consultando registros]*

{user['first_name']}, aquí tienes un resumen de tu progreso:

📊 **Estado Actual:**
• Nivel: {user_stats['level']} ⭐
• Besitos: {user_stats['besitos']:,} 💋  
• Confianza de Diana: {narrative_state.diana_trust_level}/100

🎭 **Progreso Narrativo:**
{narrative_state.current_level.value}

*[Con análisis]*

Diana {self._get_diana_opinion(narrative_state.diana_trust_level)}
        """.strip()

        keyboard = [
            [InlineKeyboardButton("📊 Ver perfil completo", callback_data="profile")],
            [InlineKeyboardButton("🎯 Próximas misiones", callback_data="mission")],
            [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            quick_profile, reply_markup=reply_markup, parse_mode="Markdown"
        )

    def _get_diana_opinion(self, trust_level: int) -> str:
        """Opinión de Diana según nivel de confianza"""

        if trust_level >= 90:
            return "está profundamente fascinada contigo."
        elif trust_level >= 70:
            return "ha notado tu dedicación especial."
        elif trust_level >= 50:
            return "está comenzando a interesarse."
        elif trust_level >= 30:
            return "observa tus acciones con curiosidad."
        else:
            return "aún está evaluando tu potencial."


# Crear handlers
command_handlers = [
    CommandHandler("help", CommandHandlers().help_command),
    CommandHandler("profile", CommandHandlers().profile_command),
    # Agregar más comandos según necesidad
]
   