from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from utils.lucien_voice import LucienVoice
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Comandos principales del bot - CON NARRATIVA INMERSIVA"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.lucien = LucienVoice()
            logger.info("✅ CommandHandlers inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando CommandHandlers: {e}")
            raise

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /help elegante - TU NARRATIVA ORIGINAL"""

        try:
            first_name = update.effective_user.first_name or "Usuario"

            help_message = f"""
{self.lucien.EMOJIS['lucien']} **Guía de Interacción**

*[Con profesionalidad]*

Estos son los comandos principales para interactuar conmigo, {first_name}:

**🎭 Comandos Básicos:**
/start - Iniciar o regresar al menú principal
/profile - Ver tu evaluación personal
/missions - Tus misiones activas
/games - Juegos de personalidad
/help - Esta guía

**💎 Comandos Avanzados:**
/shop - Tienda exclusiva de Diana
/auctions - Subastas de contenido premium
/stats - Estadísticas detalladas

**👑 Comandos VIP:** (Solo para miembros del Diván)
/divan - Acceso al círculo íntimo
/exclusive - Contenido ultra exclusivo

{self.lucien.EMOJIS['diana']} *[Diana desde las sombras]*

"*La verdadera interacción sucede a través de los botones, {first_name}. Úsalos.*"

*[Con elegancia]*

Lucien siempre está aquí para guiarte en tu camino hacia... conocer mejor a Diana.
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🎭 Menú Principal", callback_data="main_menu")],
                [InlineKeyboardButton("🎯 Empezar Misiones", callback_data="missions")],
                [InlineKeyboardButton("👤 Ver Mi Perfil", callback_data="profile")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                help_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en help_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando ayuda")

    async def profile_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /profile directo - FUSIONADO"""

        try:
            user_data = {
                "telegram_id": update.effective_user.id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name or "Usuario",
                "last_name": update.effective_user.last_name,
            }

            logger.info(f"🔍 Comando /profile de {user_data['first_name']}")

            # Obtener datos de forma segura
            try:
                user = self.user_service.get_or_create_user(user_data)  # Cambié método
                narrative_state = self.user_service.get_or_create_narrative_state(user.id)
                user_stats = self.user_service.get_user_detailed_stats(user.id)
            except Exception as e:
                logger.error(f"Error obteniendo datos de usuario: {e}")
                # Datos por defecto si falla
                user_stats = {
                    'level': 1,
                    'besitos': 0,
                    'experience': 0,
                    'missions_completed': 0
                }
                trust_level = 0
            else:
                trust_level = getattr(narrative_state, 'diana_trust_level', 0)

            quick_profile = f"""
{self.lucien.EMOJIS['lucien']} **Evaluación Rápida**

*[Consultando registros]*

{user_data['first_name']}, aquí tienes un resumen de tu progreso:

📊 **Estado Actual:**
• **Nivel:** {user_stats['level']} ⭐
• **Besitos:** {user_stats['besitos']:,} 💋  
• **Experiencia:** {user_stats['experience']:,} XP
• **Confianza de Diana:** {trust_level}/100

🎭 **Progreso Narrativo:**
{getattr(narrative_state, 'current_level', 'Iniciando tu camino')}

*[Con análisis]*

Diana {self._get_diana_opinion(trust_level)}

{self.lucien.EMOJIS['diana']} *[Observando desde las sombras]*

"*{user_data['first_name']}... {'impresionante progreso' if trust_level > 50 else 'aún hay mucho por demostrar'}.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📊 Ver perfil completo", callback_data="profile")],
                [InlineKeyboardButton("📈 Estadísticas detalladas", callback_data="stats")],
                [InlineKeyboardButton("🎯 Próximas misiones", callback_data="missions")],
                [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                quick_profile, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en profile_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando perfil")

    async def missions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /missions directo - NUEVO"""

        try:
            first_name = update.effective_user.first_name or "Usuario"
            user_id = update.effective_user.id

            logger.info(f"🔍 Comando /missions de {first_name}")

            missions_message = f"""
{self.lucien.EMOJIS['lucien']} **Misiones Activas**

*[Con propósito]*

{first_name}, Diana ha preparado desafíos especiales para ti...

🎯 **Misiones Disponibles:**

🌅 **Misión Diaria**
• Interactuar con Diana hoy
• Recompensa: 10 Besitos 💋
• Estado: Disponible

🎭 **Conocer a Diana**
• Explorar todas las introducciones
• Recompensa: 25 Besitos + Acceso especial
• Estado: En progreso

💎 **Camino al VIP**
• Completar 5 misiones principales
• Recompensa: Token VIP gratuito
• Estado: 0/5

{self.lucien.EMOJIS['diana']} *[Con expectativa]*

"*Cada misión completada me acerca más a ti, {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🎯 Ver todas las misiones", callback_data="missions")],
                [InlineKeyboardButton("🏆 Mis logros", callback_data="achievements")],
                [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                missions_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en missions_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando misiones")

    async def stats_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /stats directo - NUEVO"""

        try:
            first_name = update.effective_user.first_name or "Usuario"

            stats_message = f"""
📊 **Estadísticas de {first_name}**

{self.lucien.EMOJIS['lucien']} *[Consultando registros detallados]*

"*Aquí tienes tu expediente completo...*"

🎯 **Progreso General:**
• Nivel: 1 ⭐
• Experiencia: 0 XP
• Besitos: 0 💋

🏆 **Logros:**
• Primer contacto: ✅
• Explorador: ❌ (Nivel 2 requerido)
• Dedicado: ❌ (50 Besitos requeridos)

🎮 **Actividad:**
• Misiones completadas: 0
• Juegos jugados: 0
• Días activo: 1

{self.lucien.EMOJIS['diana']} *[Evaluando]*

"*{first_name} está... comenzando su camino. Hay potencial.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📊 Ver perfil completo", callback_data="profile")],
                [InlineKeyboardButton("🎯 Mejorar estadísticas", callback_data="missions")],
                [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                stats_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en stats_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando estadísticas")

    async def shop_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /shop directo - NUEVO"""

        try:
            first_name = update.effective_user.first_name or "Usuario"

            shop_message = f"""
🛍️ **Tienda Exclusiva de Diana**

{self.lucien.EMOJIS['diana']} *[Con aire comercial seductor]*

"*{first_name}... quieres ver mis... ofertas especiales.*"

*[Con sonrisa tentadora]*

💎 **Colecciones Disponibles:**

📸 **Fotos Exclusivas**
• Sesión "Elegancia Nocturna"
• Precio: 50 Besitos 💋
• Estado: Disponible

🎥 **Videos Personalizados**
• Saludo con tu nombre
• Precio: 100 Besitos 💋
• Estado: Disponible

✨ **Experiencias Premium**
• Chat privado 30 min
• Precio: 200 Besitos 💋
• Estado: Solo VIP

{self.lucien.EMOJIS['lucien']} *[Con discreción]*

"*Los precios reflejan la exclusividad, {first_name}.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🛍️ Explorar tienda", callback_data="shop")],
                [InlineKeyboardButton("💰 ¿Cómo ganar besitos?", callback_data="earn_besitos")],
                [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                shop_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en shop_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando tienda")

    def _get_diana_opinion(self, trust_level: int) -> str:
        """Opinión de Diana según nivel de confianza - TU LÓGICA ORIGINAL"""

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

    async def _send_error_message(self, update: Update, context: str) -> None:
        """Envía mensaje de error elegante"""
        
        error_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con disculpas profesionales]*

"*Ha ocurrido un inconveniente técnico. Diana me pide que te asegure que esto se resolverá pronto.*"

**Contexto:** {context}

*[Con aire tranquilizador]*
"*Usa /start para continuar.*"
        """.strip()

        try:
            await update.message.reply_text(error_message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {e}")

    # === VERIFICACIÓN DE ADMIN ===
    
    def _is_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es administrador"""
        import os
        
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            return False
        
        try:
            admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
            return user_id in admin_ids
        except Exception as e:
            logger.error(f"Error verificando admin: {e}")
            return False

    async def admin_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /admin - NUEVO"""

        try:
            user_id = update.effective_user.id
            first_name = update.effective_user.first_name or "Usuario"

            if not self._is_admin(user_id):
                await update.message.reply_text(
                    f"{self.lucien.EMOJIS['lucien']} *[Con disculpas]*\n\n"
                    f"Lo siento {first_name}, pero no tienes permisos de administrador."
                )
                return

            admin_message = f"""
👑 **Panel de Administrador**

{self.lucien.EMOJIS['diana']} *[Diana aparece con autoridad]*

"*{first_name}... mi administrador de confianza.*"

*[Con aire ejecutivo]*

🔧 **Controles Disponibles:**
• Gestión de usuarios
• Revisar registros
• Configuración del bot

{self.lucien.EMOJIS['lucien']} *[A la espera de tus órdenes]*
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👥 Usuarios", callback_data="manage_users")],
                [InlineKeyboardButton("📝 Registros", callback_data="view_logs")],
                [InlineKeyboardButton("⚙️ Ajustes", callback_data="bot_settings")],
                [InlineKeyboardButton("🎭 Menú principal", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                admin_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en admin_command: {e}", exc_info=True)
            await self._send_error_message(update, "Error mostrando panel de administrador")
