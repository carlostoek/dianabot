from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StartHandler:
    """Handler del comando /start - Con debug completo"""

    def __init__(self):
        logger.info("🔍 Inicializando StartHandler...")
        
        try:
            logger.info("🔍 Importando UserService...")
            from services.user_service import UserService
            self.user_service = UserService()
            logger.info("✅ UserService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando UserService: {e}")
            self.user_service = None

        try:
            logger.info("🔍 Importando ChannelService...")
            from services.channel_service import ChannelService
            self.channel_service = ChannelService()
            logger.info("✅ ChannelService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando ChannelService: {e}")
            self.channel_service = None

        try:
            logger.info("🔍 Importando LucienVoice...")
            from utils.lucien_voice import LucienVoice
            self.lucien = LucienVoice()
            logger.info("✅ LucienVoice inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando LucienVoice: {e}")
            self.lucien = None

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /start - Con debug completo"""
        
        logger.info("🔍 Iniciando handle_start...")
        
        try:
            # Verificar que tenemos update válido
            if not update or not update.effective_user:
                logger.error("❌ Update o effective_user es None")
                await self._send_simple_error(update)
                return

            logger.info(f"🔍 Usuario: {update.effective_user.id} - {update.effective_user.first_name}")

            # Verificar servicios
            if not self.user_service:
                logger.error("❌ UserService no disponible")
                await self._send_simple_error(update)
                return

            # Extraer datos del usuario
            logger.info("🔍 Extrayendo datos del usuario...")
            user_data = {
                "telegram_id": update.effective_user.id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name or "Usuario",
                "last_name": update.effective_user.last_name,
            }
            logger.info(f"✅ Datos extraídos: {user_data}")

            # Verificar si es token VIP
            if context.args and len(context.args) > 0:
                logger.info(f"🔍 Args detectados: {context.args}")
                if context.args[0].startswith("vip_token_"):
                    token = context.args[0].replace("vip_token_", "")
                    logger.info(f"🔍 Token VIP detectado: {token}")
                    await self._handle_vip_token(update, context, user_data, token)
                    return

            # Crear o obtener usuario
            logger.info("🔍 Creando/obteniendo usuario...")
            user = self.user_service.get_or_create_user(user_data)
            logger.info(f"✅ Usuario obtenido: {user}")

            logger.info("🔍 Obteniendo narrative_state...")
            narrative_state = self.user_service.get_or_create_narrative_state(user.id)
            logger.info(f"✅ Narrative state obtenido: {narrative_state}")

            # Verificar si es usuario nuevo o returning
            is_new = getattr(user, 'created_today', False)
            logger.info(f"🔍 Usuario nuevo: {is_new}")

            if is_new:
                logger.info("🔍 Enviando experiencia de usuario nuevo...")
                await self._send_new_user_experience(update, context, user, narrative_state)
            else:
                logger.info("🔍 Enviando experiencia de usuario recurrente...")
                await self._send_returning_user_experience(update, context, user, narrative_state)

            logger.info("✅ handle_start completado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en handle_start: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_new_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Experiencia para usuarios nuevos - SIMPLIFICADA para debug"""
        
        logger.info("🔍 Iniciando _send_new_user_experience...")
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            logger.info(f"🔍 Nombre: {first_name}")

            # Mensaje simple sin emojis complejos por ahora
            welcome_message = f"""
🎭 *¡Bienvenido {first_name}!*

Has llegado al bot de Diana. 

Soy Lucien, su mayordomo personal. Diana está... interesada en conocerte.

¿Qué te gustaría hacer?
            """.strip()

            keyboard = [
                [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
                [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
                [InlineKeyboardButton("🔥 Explorar el bot", callback_data="intro_bot")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            logger.info("🔍 Enviando mensaje de bienvenida...")
            await update.message.reply_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )
            logger.info("✅ Mensaje enviado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en _send_new_user_experience: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_returning_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Experiencia para usuarios recurrentes - SIMPLIFICADA"""
        
        logger.info("🔍 Iniciando _send_returning_user_experience...")
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            return_message = f"""
🎭 *¡{first_name}, has regresado!*

Diana me comentó que has estado... observándote.

Tu progreso no ha pasado desapercibido.

¿Qué deseas hacer hoy?
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👤 Mi Perfil", callback_data="profile")],
                [InlineKeyboardButton("🎯 Misiones", callback_data="missions")],
                [InlineKeyboardButton("🔥 Contenido Premium", callback_data="premium")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            logger.info("🔍 Enviando mensaje de regreso...")
            await update.message.reply_text(
                return_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )
            logger.info("✅ Mensaje enviado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en _send_returning_user_experience: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _handle_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict,
        token: str,
    ) -> None:
        """Maneja tokens VIP - SIMPLIFICADO"""
        
        logger.info(f"🔍 Procesando token VIP: {token}")
        
        try:
            # Por ahora, mensaje simple
            await update.message.reply_text(
                f"🎭 Token VIP detectado: {token}\n\n"
                "Esta funcionalidad está en desarrollo.",
                parse_mode="Markdown"
            )
            logger.info("✅ Respuesta VIP enviada")
            
        except Exception as e:
            logger.error(f"❌ Error en _handle_vip_token: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_simple_error(self, update: Update) -> None:
        """Envía mensaje de error simple"""
        try:
            if update and update.message:
                await update.message.reply_text(
                    "🎭 Ha ocurrido un error técnico.\n\n"
                    "Por favor intenta de nuevo con /start"
                )
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de error: {e}")
            
