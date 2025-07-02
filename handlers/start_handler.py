from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from services.channel_service import ChannelService
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StartHandler:
    """Handler del comando /start - Primera impresión ESPECTACULAR"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.channel_service = ChannelService()
            self.lucien = LucienVoice()
        except Exception as e:
            logger.error(f"Error inicializando StartHandler: {e}")
            raise

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /start - Onboarding seductor"""
        try:
            # Validación de entrada
            if not update.effective_user:
                logger.error("Update sin usuario efectivo")
                return

            user_data = self._extract_user_data(update.effective_user)

            # Verificar si es token VIP
            if context.args and len(context.args) > 0:
                if context.args[0].startswith("vip_token_"):
                    token = context.args[0].replace("vip_token_", "")
                    await self._handle_vip_token(update, context, user_data, token)
                    return

            # Crear o obtener usuario
            user = self.user_service.get_or_create_user(user_data)
            narrative_state = self.user_service.get_or_create_narrative_state(user.id)

            # Verificar si es usuario nuevo o returning
            if getattr(user, 'created_today', False):
                await self._send_new_user_experience(update, context, user, narrative_state)
            else:
                await self._send_returning_user_experience(
                    update, context, user, narrative_state
                )

        except Exception as e:
            logger.error(f"Error en handle_start: {e}")
            await self._send_error_message(update, "Error procesando comando /start")

    def _extract_user_data(self, user) -> Dict[str, Any]:
        """Extrae datos del usuario de forma segura"""
        return {
            "telegram_id": user.id,
            "username": getattr(user, 'username', None),
            "first_name": getattr(user, 'first_name', 'Usuario'),
            "last_name": getattr(user, 'last_name', None),
        }

    async def _send_new_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Experiencia MAGNÉTICA para usuarios nuevos"""
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            welcome_message = f"""
{self.lucien.EMOJIS['diana']} *Una figura elegante emerge de las sombras...*

"*{first_name}... así que finalmente has llegado hasta mí.*"

{self.lucien.EMOJIS['lucien']} *[Lucien se acerca con una reverencia]*

Permíteme presentarme: soy **Lucien**, mayordomo personal de Diana. Ella me ha encargado evaluar a quienes buscan... acercarse a ella.

*[Con aire misterioso]*

Diana no es una mujer ordinaria. Es selectiva, inteligente, y tiene poco tiempo para los... triviales. Pero hay algo en ti que ha captado su atención.

{self.lucien.EMOJIS['diana']} *[Diana desde las sombras]*

"*Lucien, déjame ver qué clase de persona es {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
                [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
                [InlineKeyboardButton("🔥 ¿Qué hace este bot especial?", callback_data="intro_bot")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await self._send_message(update, welcome_message, reply_markup)

        except Exception as e:
            logger.error(f"Error en _send_new_user_experience: {e}")
            await self._send_error_message(update, "Error en experiencia de usuario nuevo")

    async def _send_returning_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Experiencia para usuarios que regresan"""
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            has_divan_access = getattr(narrative_state, 'has_divan_access', False)

            if has_divan_access:
                return_message = f"""
{self.lucien.EMOJIS['diana']} *Diana aparece con una sonrisa íntima*

"*{first_name}, mi querido miembro del Diván... has regresado.*"

*[Con calidez exclusiva]*
"*Lucien me ha mantenido informada de tu... dedicación. Me complace verte de nuevo.*"

{self.lucien.EMOJIS['lucien']} *[Con reverencia especial]*

Bienvenido de vuelta al círculo íntimo, {first_name}. Diana está especialmente... receptiva hoy.
                """.strip()
            else:
                return_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con reconocimiento]*

Ah, {first_name}... regresas. Diana me comentó que ha estado... observándote.

*[Con aire conspiratorio]*
Tu progreso no ha pasado desapercibido. Cada interacción, cada decisión... todo llega a los oídos de Diana.

{self.lucien.EMOJIS['diana']} *[Una voz susurrante]*

"*Lucien, muéstrale a {first_name} las nuevas oportunidades que he preparado...*"
                """.strip()

            await self._show_main_menu(update, context, user, narrative_state, return_message)

        except Exception as e:
            logger.error(f"Error en _send_returning_user_experience: {e}")
            await self._send_error_message(update, "Error en experiencia de usuario recurrente")

    async def _handle_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict,
        token: str,
    ) -> None:
        """Maneja tokens VIP con experiencia especial"""
        try:
            # Validar token
            if not token or len(token) < 5:
                await self._send_invalid_token_message(update, user_data.get('first_name', 'Usuario'))
                return

            user = self.user_service.get_or_create_user(user_data)
            token_result = self.channel_service.validate_and_use_vip_token(token, user.id)

            if not token_result.get("success"):
                await self._send_token_error_message(
                    update, 
                    user_data.get('first_name', 'Usuario'),
                    token_result.get('error', 'Token no válido')
                )
                return

            await self._send_vip_welcome_message(update, user_data, token_result)

        except Exception as e:
            logger.error(f"Error en _handle_vip_token: {e}")
            await self._send_error_message(update, "Error procesando token VIP")

    async def _send_vip_welcome_message(
        self, 
        update: Update, 
        user_data: Dict, 
        token_result: Dict
    ) -> None:
        """Envía mensaje de bienvenida VIP"""
        first_name = user_data.get('first_name', 'Usuario')
        channel_name = token_result.get('channel_name', 'Canal VIP')
        channel_id = token_result.get('channel_telegram_id')

        vip_welcome = f"""
{self.lucien.EMOJIS['diana']} *Diana aparece con una sonrisa exclusiva*

"*{first_name}... has sido personalmente invitado a mi círculo más íntimo.*"

*[Con elegancia suprema]*
"*No cualquiera recibe acceso directo al Diván. Alguien habló muy bien de ti...*"

{self.lucien.EMOJIS['lucien']} *[Con reverencia máxima]*

¡Felicitaciones! Has sido admitido directamente al **Diván de Diana** - el espacio más exclusivo y íntimo.

✨ **Acceso VIP Otorgado**
👑 **Canal:** {channel_name}
🔥 **Privilegios:** Contenido exclusivo, subastas premium, interacción directa

*[Con aire conspiratorio]*
Diana está... especialmente interesada en conocerte.
        """.strip()

        keyboard = []
        
        # Solo agregar botón de canal si tenemos ID válido
        if channel_id:
            keyboard.append([
                InlineKeyboardButton(
                    "💎 Ingresar al Diván",
                    url=f"https://t.me/c/{channel_id}",
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("🎭 Mi Perfil VIP", callback_data="profile_vip")],
            [InlineKeyboardButton("🔥 Explorar Privilegios", callback_data="vip_privileges")],
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_message(update, vip_welcome, reply_markup)

    async def _send_message(
        self, 
        update: Update, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """Envía mensaje de forma segura"""
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text, reply_markup=reply_markup, parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text, reply_markup=reply_markup, parse_mode="Markdown"
                )
            else:
                logger.error("Update sin message ni callback_query")
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")

    async def _send_error_message(self, update: Update, error_context: str) -> None:
        """Envía mensaje de error elegante"""
        error_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con disculpas profesionales]*

Ha ocurrido un inconveniente técnico. Diana me pide que te asegure que esto se resolverá pronto.

Usa /start para continuar.
        """.strip()

        try:
            await self._send_message(update, error_message)
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {e}")

    # ... resto de métodos con validaciones similares
                    
