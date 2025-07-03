from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from utils.lucien_voice import LucienVoice
from config.settings import settings
import logging
from typing import Dict, Any, List
import os

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

    def _is_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es administrador"""
        admin_ids: List[int] = []

        env_admins = os.getenv("ADMIN_IDS")
        if env_admins:
            try:
                admin_ids.extend(int(uid.strip()) for uid in env_admins.split(",") if uid.strip())
            except ValueError:
                pass

        settings_admins = getattr(settings, "ADMIN_IDS", None)
        if isinstance(settings_admins, str):
            try:
                admin_ids.extend(int(uid.strip()) for uid in settings_admins.split(",") if uid.strip())
            except ValueError:
                pass
        elif isinstance(settings_admins, list):
            try:
                admin_ids.extend(int(uid) for uid in settings_admins)
            except Exception:
                pass

        return user_id in admin_ids

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja todos los callbacks"""
        
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            user_id = update.effective_user.id


            
            # Routing de callbacks
            if callback_data == "profile":
                await self._handle_profile(update, context)
            elif callback_data == "missions":
                await self._handle_missions(update, context)
            elif callback_data == "premium":
                await self._handle_premium(update, context)
            elif callback_data == "vip_preview":
                await self._handle_vip_preview(update, context)
            elif callback_data == "get_vip":
                await self._handle_get_vip(update, context)
            elif callback_data == "testimonials":
                await self._handle_testimonials(update, context)
            elif callback_data == "get_vip_urgent":
                await self._handle_get_vip_urgent(update, context)
            elif callback_data == "get_vip_now":
                await self._handle_get_vip_now(update, context)
            elif callback_data.startswith("intro_"):
                await self._handle_intro_callbacks(update, context, callback_data)
            elif callback_data == "back_to_menu":
                await self._handle_back_to_menu(update, context)
            elif callback_data == "back_to_start":
                await self._handle_back_to_start(update, context)
            elif callback_data == "back_to_profile":
                await self._handle_back_to_profile(update, context)
            elif callback_data == "back_to_missions":
                await self._handle_back_to_missions(update, context)
            elif callback_data == "back_to_premium":
                await self._handle_back_to_premium(update, context)
            elif callback_data == "main_menu":
                await self._handle_main_menu(update, context)
            elif callback_data == "home":
                await self._handle_home(update, context)
            elif callback_data == "cancel":
                await self._handle_cancel(update, context)
            elif callback_data == "go_back":
                await self._handle_go_back(update, context)
            elif callback_data == "back_to_intro":
                await self._handle_back_to_intro(update, context)
            elif callback_data == "back_to_vip_options":
                await self._handle_back_to_vip_options(update, context)
            elif callback_data == "exit_confirm":
                await self._handle_exit_confirm(update, context)
            elif callback_data == "goodbye":
                await self._handle_goodbye(update, context)
            elif callback_data == "continue_exploring":
                await self._handle_continue_exploring(update, context)
            elif callback_data == "retry_last_action":
                await self._handle_retry_last_action(update, context)
            elif callback_data == "stats":
                await self._handle_stats(update, context)
            elif callback_data == "my_missions":
                await self._handle_my_missions(update, context)
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

    async def _handle_get_vip(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Proceso principal para obtener acceso VIP"""

        first_name = update.effective_user.first_name or "Usuario"
        user_id = update.effective_user.id

        message = f"""
👑 **Proceso de Acceso VIP**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana se acerca con elegancia suprema]*

"*{first_name}... has tomado una decisión muy... inteligente.*"

*[Con aire exclusivo]*

💎 **Caminos al Diván de Diana:**

🎫 **1. Token de Invitación VIP**
• Código especial de acceso
• Entrada inmediata
• Para invitados seleccionados
• **¿Tienes un token?**

🎯 **2. Ruta de Mérito**
• Completar 10 misiones especiales
• Demostrar dedicación a Diana
• Progreso actual: 0/10
• **Tiempo estimado: 3-5 días**

⚡ **3. Acceso Premium**
• Contribución directa al proyecto
• Acceso instantáneo
• Beneficios adicionales exclusivos
• **Disponible ahora**

🎮 **4. Desafío de Diana**
• Superar pruebas especiales
• Solo para los más... audaces
• Diana evalúa personalmente
• **¿Te atreves?**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien con aire conspirativo]*

"*Diana me ha pedido mencionar que los lugares en el Diván son... limitados.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🎫 Tengo un Token VIP", callback_data="enter_vip_token")],
            [InlineKeyboardButton("🎯 Ruta de Mérito", callback_data="merit_path")],
            [InlineKeyboardButton("⚡ Acceso Premium", callback_data="premium_access")],
            [InlineKeyboardButton("🎮 Desafío de Diana", callback_data="diana_challenge")],
            [InlineKeyboardButton("❓ ¿Cuál me recomiendas?", callback_data="vip_recommendation")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="premium")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_vip_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Muestra vista previa del contenido VIP"""

        first_name = update.effective_user.first_name or "Usuario"

        message = f"""
📸 **Vista Previa VIP**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece en penumbras seductoras]*

"*{first_name}... quieres un pequeño... adelanto.*"

*[Con sonrisa misteriosa]*

🔥 **Contenido Exclusivo del Diván:**

📱 **Fotos Íntimas**
• Sesiones fotográficas privadas
• Outfits exclusivos solo para VIPs
• Behind the scenes

🎥 **Videos Personalizados**
• Saludos con tu nombre
• Experiencias inmersivas
• Contenido interactivo

💬 **Chat Directo**
• Conversaciones privadas con Diana
• Respuestas personalizadas
• Acceso 24/7

🎪 **Subastas Exclusivas**
• Experiencias únicas
• Objetos personales
• Encuentros virtuales

*[Susurrando seductoramente]*

"*Esto es solo... una pequeña muestra de lo que te espera.*"

⚠️ **Vista previa censurada** - El contenido completo solo está disponible para miembros VIP.
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔥 ¡Necesito Acceso YA!", callback_data="get_vip_urgent")],
            [InlineKeyboardButton("👑 Proceso VIP Normal", callback_data="get_vip")],
            [InlineKeyboardButton("💬 Ver Testimonios", callback_data="testimonials")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="premium")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_testimonials(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Muestra testimonios de usuarios VIP"""

        message = f"""
💬 **Testimonios VIP del Diván**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien presenta con orgullo]*

"*Permíteme compartir las palabras de quienes ya han experimentado la... magia de Diana.*"

---

👤 **Carlos, miembro VIP desde hace 3 meses:**
*"Diana cambió completamente mi perspectiva. No es solo contenido, es una experiencia que te transforma. El Diván es... adictivo en el mejor sentido."*
⭐⭐⭐⭐⭐

👤 **Miguel, Diván Premium:**
*"Nunca pensé que podría tener acceso tan directo a alguien como Diana. Sus respuestas personalizadas me hacen sentir especial. Vale cada peso invertido."*
⭐⭐⭐⭐⭐

👤 **Alejandro, VIP Gold:**
*"Las subastas son increíbles. Gané una videollamada personalizada y fue... indescriptible. Diana sabe exactamente cómo hacer sentir único a cada uno."*
⭐⭐⭐⭐⭐

👤 **Roberto, miembro del círculo íntimo:**
*"Al principio era escéptico, pero Diana y su sistema son auténticos. La narrativa, los juegos, todo está perfectamente diseñado. Es arte erótico."*
⭐⭐⭐⭐⭐

---

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece brevemente]*

"*No me gusta presumir, pero... mis chicos me adoran.*"

*[Con sonrisa pícara]*

"*¿Serás el próximo en escribir un testimonio?*"

📊 **Estadísticas VIP:**
• 94% de satisfacción
• 87% renueva su membresía
• 0 usuarios arrepentidos
• Tiempo promedio de respuesta: 2.3 horas
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔥 ¡Quiero Ser el Siguiente!", callback_data="get_vip_now")],
            [InlineKeyboardButton("📧 Contactar a un Miembro", callback_data="contact_member")],
            [InlineKeyboardButton("📊 Ver Más Estadísticas", callback_data="vip_stats")],
            [InlineKeyboardButton("👑 Proceso de Acceso", callback_data="get_vip")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="premium")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_get_vip_urgent(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja acceso VIP urgente después de vista previa"""

        first_name = update.effective_user.first_name or "Usuario"

        message = f"""
🔥 **ACCESO VIP URGENTE**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana sonríe con satisfacción]*

"*{first_name}... veo que la vista previa causó el efecto deseado.*"

*[Con aire triunfante]*

"*Me encanta cuando alguien sabe reconocer... la calidad.*"

⚡ **OPCIONES DE ACCESO INMEDIATO:**

🎫 **Token VIP**
• Si tienes código de invitación
• Acceso en 30 segundos
• **DISPONIBLE AHORA**

💳 **Premium Express**
• Pago directo
• Activación automática
• Sin tiempos de espera
• **RECOMENDADO**

🎯 **Fast-Track de Misiones**
• Misiones aceleradas
• 3x velocidad normal
• Acceso en 24h
• **PARA DEDICADOS**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien susurra]*

"*Diana está... especialmente receptiva hoy. Es el momento perfecto.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🎫 Usar Token Ahora", callback_data="enter_vip_token")],
            [InlineKeyboardButton("💳 Premium Express", callback_data="premium_express")],
            [InlineKeyboardButton("🎯 Fast-Track", callback_data="fast_track_missions")],
            [InlineKeyboardButton("💬 Hablar con Diana", callback_data="talk_to_diana")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="vip_preview")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_get_vip_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Callback directo desde testimonios"""

        message = f"""
🚀 **¡PERFECTO TIMING!**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece emocionada]*

"*¡Me encanta la decisión rápida! Eso me dice que sabes lo que quieres.*"

*[Con aire seductor]*

"*Los testimonios no mienten... y tú serás el próximo en escribir uno.*"

🎯 **Proceso acelerado activado:**
        """.strip()

        keyboard = [
            [InlineKeyboardButton("👑 Ver Opciones VIP", callback_data="get_vip")],
            [InlineKeyboardButton("⚡ Acceso Inmediato", callback_data="premium_express")],
            [InlineKeyboardButton("🎫 Tengo Token", callback_data="enter_vip_token")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

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

    # === CALLBACKS DE NAVEGACIÓN ===

    async def _handle_back_to_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Regresa al menú principal - detecta si es admin"""

        first_name = update.effective_user.first_name or "Usuario"
        user_id = update.effective_user.id

        is_admin = self._is_admin(user_id)

        if is_admin:
            message = f"""
👑 **Panel de Administrador**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece con aire autoritario]*

"*{first_name}... mi administrador de confianza.*"

*[Con sonrisa cómplice]*

"*¿Qué necesitas gestionar hoy?*"

🔧 **CONTROLES DE ADMIN DISPONIBLES**
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👤 Mi Perfil", callback_data="profile")],
                [InlineKeyboardButton("🎯 Misiones", callback_data="missions")],
                [InlineKeyboardButton("⚙️ Panel Admin", callback_data="admin_panel")],
                [InlineKeyboardButton("👥 Gestionar Usuarios", callback_data="manage_users")],
                [InlineKeyboardButton("📊 Estadísticas Bot", callback_data="bot_stats")],
                [InlineKeyboardButton("🎫 Crear Tokens VIP", callback_data="create_vip_tokens")],
                [InlineKeyboardButton("📢 Enviar Broadcast", callback_data="send_broadcast")],
                [InlineKeyboardButton("🔧 Configuración", callback_data="admin_settings")],
            ]
        else:
            message = f"""
🎭 **Menú Principal**

¡{first_name}, has regresado!

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

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _handle_back_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa al inicio - mismo que menú principal"""
        await self._handle_back_to_menu(update, context)

    async def _handle_back_to_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa al perfil"""
        await self._handle_profile(update, context)

    async def _handle_back_to_missions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa a misiones"""
        await self._handle_missions(update, context)

    async def _handle_back_to_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa a premium"""
        await self._handle_premium(update, context)

    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Alias para back_to_menu"""
        await self._handle_back_to_menu(update, context)

    async def _handle_home(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa al inicio/home"""
        await self._handle_back_to_menu(update, context)

    async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Cancela operación actual y regresa al menú"""

        message = f"""
❌ **Operación Cancelada**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien asiente comprensivamente]*

"*No hay problema. Diana siempre dice que es mejor estar seguro.*"

*[Con aire alentador]*

"*Cuando estés listo, estaremos aquí.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="back_to_menu")],
            [InlineKeyboardButton("🔄 Intentar de Nuevo", callback_data="retry_last_action")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _handle_go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Navegación genérica hacia atrás"""
        await self._handle_back_to_menu(update, context)

    # NAVEGACIÓN ESPECÍFICA DE SECCIONES

    async def _handle_back_to_intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa a las introducciones"""

        first_name = update.effective_user.first_name or "Usuario"

        message = f"""
✨ **Introducciones**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien hace una reverencia]*

"*{first_name}, permíteme ofrecerte las presentaciones apropiadas...*"

*[Con aire ceremonioso]*

"*¿A quién te gustaría conocer mejor?*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
            [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
            [InlineKeyboardButton("🔥 ¿Qué hace este bot especial?", callback_data="intro_bot")],
            [InlineKeyboardButton("⬅️ Menú Principal", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _handle_back_to_vip_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Regresa a opciones VIP"""
        await self._handle_get_vip(update, context)

    # NAVEGACIÓN CON CONFIRMACIÓN

    async def _handle_exit_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Confirma si quiere salir"""

        message = f"""
🚪 **¿Seguro que quieres salir?**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana aparece con aire melancólico]*

"*¿Ya te vas? Justo cuando las cosas se estaban poniendo... interesantes.*"

*[Con sonrisa traviesa]*

"*Pero entiendo. A veces necesitas... procesar lo que has visto.*"

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien con aire profesional]*

"*Recuerda que siempre puedes regresar con /start*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🏠 No, quedarme en el menú", callback_data="back_to_menu")],
            [InlineKeyboardButton("🔄 Continuar explorando", callback_data="continue_exploring")],
            [InlineKeyboardButton("👋 Sí, salir por ahora", callback_data="goodbye")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _handle_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mensaje de despedida"""

        first_name = update.effective_user.first_name or "Usuario"

        message = f"""
👋 **Hasta pronto, {first_name}**

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana se despide con elegancia]*

"*Ha sido un placer conocerte, {first_name}. Espero verte pronto...*"

*[Con aire misterioso]*

"*Recuerda: siempre estaré aquí cuando decidas regresar.*"

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien hace una reverencia final]*

"*Que tengas un excelente día. Diana y yo estaremos... esperando.*"

💫 **Para regresar:** Usa /start en cualquier momento
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔄 ¡Espera, no me voy!", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # === NAVEGACIÓN ADICIONAL ÚTIL ===

    async def _handle_continue_exploring(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Continuar explorando tras confirmación"""
        await self._handle_back_to_menu(update, context)

    async def _handle_retry_last_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reintenta la última acción"""
        await self._handle_back_to_menu(update, context)

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

    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Muestra estadísticas detalladas del usuario"""

        try:
            first_name = update.effective_user.first_name or "Usuario"
            user_id = update.effective_user.id

            # Obtener usuario de forma segura
            try:
                user_data = {
                    "telegram_id": user_id,
                    "username": update.effective_user.username,
                    "first_name": first_name,
                    "last_name": update.effective_user.last_name,
                }
                user = self.user_service.get_or_create_user(user_data)

                # Obtener estadísticas de forma segura
                level = getattr(user, "level", 1)
                besitos = getattr(user, "besitos", 0)
                experience = getattr(user, "experience", 0)
                is_vip = getattr(user, "is_vip", False)
                created_at = getattr(user, "created_at", "Desconocido")

                # Calcular días desde registro
                if hasattr(user, "created_at") and user.created_at:
                    from datetime import datetime

                    days_registered = (datetime.utcnow() - user.created_at).days
                else:
                    days_registered = 0

            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                # Valores por defecto
                level = 1
                besitos = 0
                experience = 0
                is_vip = False
                days_registered = 0

            # Calcular progreso al siguiente nivel
            exp_needed = level * 100
            exp_progress = (experience % 100) if experience > 0 else 0
            progress_bar = "█" * (exp_progress // 10) + "░" * (10 - (exp_progress // 10))

            message = f"""
📊 **Estadísticas Detalladas de {first_name}**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien consulta un elegante dossier]*

"*Veamos tu expediente completo...*"

👤 **Información General:**
• **Nombre:** {first_name}
• **ID:** {user_id}
• **Días registrado:** {days_registered}
• **Estado:** {'👑 VIP Premium' if is_vip else '🆓 Usuario Gratuito'}

🎯 **Progreso de Gamificación:**
• **Nivel Actual:** {level}
• **Experiencia:** {experience} XP
• **Besitos:** {besitos} 💋

📈 **Progreso al Siguiente Nivel:**
{progress_bar} {exp_progress}/100 XP

🏆 **Logros Desbloqueados:**
{'✅ Primer Contacto' if days_registered > 0 else '❌ Primer Contacto'}
{'✅ Explorador' if level >= 2 else '❌ Explorador (Nivel 2)'}
{'✅ Dedicado' if besitos >= 50 else '❌ Dedicado (50 Besitos)'}
{'✅ Miembro VIP' if is_vip else '❌ Miembro VIP'}

🎮 **Actividad:**
• Misiones completadas: {level - 1}
• Interacciones totales: {experience // 10}
• Puntuación Diana: {besitos // 10}/10

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana observa desde las sombras]*

"*{'Impresionante dedicación' if level > 3 else 'Buen progreso'}, {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🏆 Ver Logros", callback_data="achievements")],
                [InlineKeyboardButton("📈 Historial", callback_data="user_history")],
                [InlineKeyboardButton("🎯 Mejorar Stats", callback_data="improve_stats")],
                [InlineKeyboardButton("⬅️ Volver al Perfil", callback_data="back_to_profile")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_stats: {e}", exc_info=True)
            await self._send_error_message(update)

    async def _handle_my_missions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Muestra misiones específicas del usuario"""

        try:
            first_name = update.effective_user.first_name or "Usuario"
            user_id = update.effective_user.id

            # Obtener progreso del usuario
            try:
                user_data = {
                    "telegram_id": user_id,
                    "username": update.effective_user.username,
                    "first_name": first_name,
                    "last_name": update.effective_user.last_name,
                }
                user = self.user_service.get_or_create_user(user_data)
                level = getattr(user, "level", 1)
                besitos = getattr(user, "besitos", 0)

            except Exception as e:
                logger.error(f"Error obteniendo usuario para misiones: {e}")
                level = 1
                besitos = 0

            # Simular misiones basadas en progreso
            missions_completed = level - 1
            daily_completed = besitos >= 10

            message = f"""
🎯 **Mis Misiones - {first_name}**

{self.lucien.EMOJIS.get('lucien', '🎭')} *[Lucien revisa tu progreso personal]*

"*Veamos qué tareas Diana ha preparado específicamente para ti...*"

📋 **MISIONES ACTIVAS:**

🌅 **Misión Diaria**
• Descripción: Interactuar con Diana hoy
• Progreso: {'✅ Completada' if daily_completed else '⏳ Pendiente'}
• Recompensa: 10 Besitos 💋
• {'🎁 ¡Reclamar!' if daily_completed else '🔄 En progreso'}

🎭 **Conociendo a Diana**
• Descripción: Explorar todas las introducciones
• Progreso: {'✅ Completada' if level >= 2 else '⏳ 2/3 completadas'}
• Recompensa: 25 Besitos + Acceso especial
• {'🎁 ¡Completada!' if level >= 2 else '🔄 Continuar'}

💎 **Camino al VIP**
• Descripción: Completar 5 misiones principales
• Progreso: {missions_completed}/5
• Recompensa: Token VIP gratuito
• {'🎁 ¡Desbloqueada!' if missions_completed >= 5 else f'🔄 {5 - missions_completed} restantes'}

🔥 **Seducir a Diana**
• Descripción: Alcanzar 100 Besitos
• Progreso: {besitos}/100 💋
• Recompensa: Contenido exclusivo
• {'🎁 ¡Logrado!' if besitos >= 100 else f'🔄 {100 - besitos} besitos restantes'}

📈 **MISIONES COMPLETADAS:** {missions_completed}

{self.lucien.EMOJIS.get('diana', '👑')} *[Diana susurra]*

"*Cada misión completada me acerca más a ti...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🎁 Reclamar Recompensas", callback_data="claim_rewards")],
                [InlineKeyboardButton("🔄 Actualizar Progreso", callback_data="refresh_missions")],
                [InlineKeyboardButton("💡 Consejos de Misiones", callback_data="mission_tips")],
                [InlineKeyboardButton("⬅️ Volver al Perfil", callback_data="back_to_profile")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_my_missions: {e}", exc_info=True)
            await self._send_error_message(update)

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
            
