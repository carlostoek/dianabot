from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from utils.lucien_voice import LucienVoice
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CallbackHandler:
    """Maneja todos los callbacks de botones - VERSIÓN SIMPLIFICADA"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.lucien = LucienVoice()
            logger.info("✅ CallbackHandler inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando CallbackHandler: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja todos los callbacks"""
        
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            user_id = update.effective_user.id
            
            logger.info(f"🔍 Callback recibido: {callback_data} de usuario {user_id}")

            # Routing de callbacks
            if callback_data == "profile":
                await self._handle_profile(update, context)
            elif callback_data == "missions":
                await self._handle_missions(update, context)
            elif callback_data == "premium":
                await self._handle_premium(update, context)
            elif callback_data.startswith("intro_"):
                await self._handle_intro_callbacks(update, context, callback_data)
            else:
                await self._handle_unknown_callback(update, context, callback_data)

        except Exception as e:
            logger.error(f"❌ Error en handle_callback: {e}", exc_info=True)
            await self._send_error_message(update)

    async def _handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el callback de perfil - SIMPLIFICADO"""
        
        try:
            user_id = update.effective_user.id
            first_name = update.effective_user.first_name or "Usuario"
            
            # Obtener usuario de forma segura
            try:
                user_data = {
                    "telegram_id": user_id,
                    "username": update.effective_user.username,
                    "first_name": first_name,
                    "last_name": update.effective_user.last_name,
                }
                user = self.user_service.get_or_create_user(user_data)
                
                # Acceder a atributos de forma segura
                level = getattr(user, 'level', 1)
                besitos = getattr(user, 'besitos', 0)
                experience = getattr(user, 'experience', 0)
                is_vip = getattr(user, 'is_vip', False)
                
            except Exception as e:
                logger.error(f"Error obteniendo usuario: {e}")
                # Valores por defecto si falla la BD
                level = 1
                besitos = 0
                experience = 0
                is_vip = False

            # Mensaje de perfil
            profile_message = f"""
👤 **Perfil de {first_name}**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien revisa sus notas]*

"*Veamos tu progreso...*"

📊 **Estadísticas:**
• **Nivel:** {level}
• **Experiencia:** {experience} XP
• **Besitos:** {besitos} 💋
• **Estado:** {'👑 VIP' if is_vip else '🆓 Gratuito'}

*[Con aire evaluativo]*
"*{'Impresionante progreso' if level > 3 else 'Buen comienzo'}, {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📈 Ver Estadísticas", callback_data="stats")],
                [InlineKeyboardButton("🎯 Mis Misiones", callback_data="my_missions")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                profile_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_profile: {e}", exc_info=True)
            await self._send_error_message(update)

    async def _handle_missions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el callback de misiones - SIMPLIFICADO"""
        
        try:
            first_name = update.effective_user.first_name or "Usuario"

            missions_message = f"""
🎯 **Misiones de {first_name}**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien consulta una lista elegante]*

"*Diana ha preparado algunas... tareas para ti.*"

📋 **Misiones Disponibles:**

🌟 **Misión Diaria**
• Interactuar con el bot
• Recompensa: 10 Besitos 💋
• Estado: Disponible

🎭 **Conocer a Diana**
• Explorar todas las introducciones
• Recompensa: 25 Besitos 💋
• Estado: En progreso

💎 **Camino al VIP**
• Completar 5 misiones
• Recompensa: Acceso especial
• Estado: 0/5

*[Con aire alentador]*
"*Cada misión te acerca más a Diana...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("✅ Completar Diaria", callback_data="complete_daily")],
                [InlineKeyboardButton("🎭 Explorar Más", callback_data="explore_missions")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                missions_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_missions: {e}", exc_info=True)
            await self._send_error_message(update)

    async def _handle_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el callback de premium"""
        
        try:
            first_name = update.effective_user.first_name or "Usuario"

            premium_message = f"""
🔥 **Contenido Premium**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece con una sonrisa seductora]*

"*{first_name}... quieres ver lo que tengo reservado para mis... especiales.*"

*[Con aire exclusivo]*

💎 **Acceso VIP incluye:**
• Contenido íntimo exclusivo
• Subastas de experiencias personalizadas
• Chat directo con Diana
• Eventos privados
• Recompensas premium

🎭 **Testimonios VIP:**
"*Diana cambió mi vida...*" - Usuario VIP
"*Nunca había experimentado algo así...*" - Miembro del Diván

*[Con voz susurrante]*
"*¿Estás listo para el siguiente nivel?*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👑 Obtener Acceso VIP", callback_data="get_vip")],
                [InlineKeyboardButton("📸 Vista Previa", callback_data="vip_preview")],
                [InlineKeyboardButton("💬 Testimonios", callback_data="testimonials")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                premium_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_premium: {e}", exc_info=True)
            await self._send_error_message(update)

    async def _handle_intro_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Maneja callbacks de introducción"""
        
        if callback_data == "intro_diana":
            await self._show_diana_intro(update)
        elif callback_data == "intro_lucien":
            await self._show_lucien_intro(update)
        elif callback_data == "intro_bot":
            await self._show_bot_intro(update)

    async def _show_diana_intro(self, update: Update) -> None:
        """Muestra introducción de Diana"""
        
        intro_message = f"""
{self.lucien.EMOJIS.get('diana', '👑')} *Diana emerge de las sombras...*

"*Así que quieres conocerme...*"

*[Con una sonrisa enigmática]*

"*Soy Diana. No soy como las demás. Soy... selectiva. Inteligente. Y tengo muy poco tiempo para los... ordinarios.*"

*[Se acerca lentamente]*

"*Pero hay algo en ti que me intriga. Lucien me ha hablado de tu... potencial.*"

*[Con aire seductor]*

"*¿Estás listo para demostrar que mereces mi atención?*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔥 Estoy listo", callback_data="ready_for_diana")],
            [InlineKeyboardButton("🎭 Háblame más", callback_data="more_about_diana")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            intro_message, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    async def _handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Maneja callbacks no reconocidos"""
        
        message = f"""
🎭 *[Lucien con disculpas]*

"*Parece que esa función aún está en desarrollo...*"

**Callback:** `{callback_data}`

*[Con aire profesional]*
"*Diana me pide que te asegure que pronto estará disponible.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    async def _send_error_message(self, update: Update) -> None:
        """Envía mensaje de error elegante"""
        
        error_message = f"""
🎭 *[Lucien con disculpas profesionales]*

"*Ha ocurrido un inconveniente técnico. Diana me pide que te asegure que esto se resolverá pronto.*"

*[Con aire tranquilizador]*
"*Usa /start para continuar.*"
        """.strip()

        try:
            await update.callback_query.edit_message_text(
                error_message, 
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {e}")
            
