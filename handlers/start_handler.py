from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from services.user_service import UserService
from services.channel_service import ChannelService
from utils.lucien_voice import LucienVoice
from typing import Dict, Any
import re


class StartHandler:
    """Handler del comando /start - Primera impresión ESPECTACULAR"""

    def __init__(self):
        self.user_service = UserService()
        self.channel_service = ChannelService()
        self.lucien = LucienVoice()

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /start - Onboarding seductor"""

        user_data = {
            "telegram_id": update.effective_user.id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
        }

        # Verificar si es token VIP
        if context.args and len(context.args) > 0:
            if context.args[0].startswith("vip_token_"):
                token = context.args[0].replace("vip_token_", "")
                await self._handle_vip_token(update, context, user_data, token)
                return

        # Crear o obtener usuario
        user = self.user_service.create_or_update_user(user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user["id"])

        # Verificar si es usuario nuevo o returning
        if user["created_today"]:
            await self._send_new_user_experience(update, context, user, narrative_state)
        else:
            await self._send_returning_user_experience(
                update, context, user, narrative_state
            )

    async def _send_new_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
    ) -> None:
        """Experiencia MAGNÉTICA para usuarios nuevos"""

        first_name = user["first_name"]

        # MENSAJE INICIAL SEDUCTOR
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

        # BOTONES DE PRIMERA IMPRESIÓN
        keyboard = [
            [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
            [
                InlineKeyboardButton(
                    "🎭 ¿Quién es Lucien?", callback_data="intro_lucien"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 ¿Qué hace este bot especial?", callback_data="intro_bot"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _send_returning_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
    ) -> None:
        """Experiencia para usuarios que regresan"""

        first_name = user["first_name"]

        # Mensaje personalizado según progreso
        if narrative_state.has_divan_access:
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

        # Mostrar menú principal según tipo de usuario
        await self._show_main_menu(
            update, context, user, narrative_state, return_message
        )

    async def _handle_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict,
        token: str,
    ) -> None:
        """Maneja tokens VIP con experiencia especial"""

        # Crear usuario si no existe
        user = self.user_service.create_or_update_user(user_data)

        # Validar token
        token_result = self.channel_service.validate_and_use_vip_token(
            token, user["id"]
        )

        if not token_result.get("success"):
            error_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con pesar profesional]*

Me temo que hay un problema con tu invitación, {user['first_name']}.

**Error:** {token_result.get('error', 'Token no válido')}

*[Con esperanza]*
Pero no todo está perdido. Diana siempre tiene... otros caminos para quienes demuestran verdadera dedicación.
            """.strip()

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🌟 Explorar Alternativas", callback_data="explore_alternatives"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                error_message, reply_markup=reply_markup, parse_mode="Markdown"
            )
            return

        # TOKEN VÁLIDO - EXPERIENCIA VIP ÉPICA
        vip_welcome = f"""
{self.lucien.EMOJIS['diana']} *Diana aparece con una sonrisa exclusiva*

"*{user['first_name']}... has sido personalmente invitado a mi círculo más íntimo.*"

*[Con elegancia suprema]*
"*No cualquiera recibe acceso directo al Diván. Alguien habló muy bien de ti...*"

{self.lucien.EMOJIS['lucien']} *[Con reverencia máxima]*

¡Felicitaciones! Has sido admitido directamente al **Diván de Diana** - el espacio más exclusivo y íntimo.

✨ **Acceso VIP Otorgado**
👑 **Canal:** {token_result['channel_name']}
🔥 **Privilegios:** Contenido exclusivo, subastas premium, interacción directa

*[Con aire conspiratorio]*
Diana está... especialmente interesada en conocerte.
        """.strip()

        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 Ingresar al Diván",
                    url=f"https://t.me/c/{token_result['channel_telegram_id']}",
                )
            ],
            [InlineKeyboardButton("🎭 Mi Perfil VIP", callback_data="profile_vip")],
            [
                InlineKeyboardButton(
                    "🔥 Explorar Privilegios", callback_data="vip_privileges"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            vip_welcome, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _show_main_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
        intro_message: str = None,
    ) -> None:
        """Muestra menú principal diferenciado"""

        if narrative_state.has_divan_access:
            await self._show_vip_menu(
                update, context, user, narrative_state, intro_message
            )
        else:
            await self._show_free_menu(
                update, context, user, narrative_state, intro_message
            )

    async def _show_free_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
        intro_message: str = None,
    ) -> None:
        """Menú GRATUITO - Enfocado en UPGRADE a VIP"""

        if not intro_message:
            intro_message = f"""
{self.lucien.EMOJIS['lucien']} **Panel Principal**

*[Con elegancia profesional]*

¿Qué deseas explorar hoy, {user['first_name']}?

*[Con aire sugerente]*
Diana observa tus elecciones con... interés creciente.
            """.strip()

        # MENÚ ESTRATÉGICO PARA CONVERSIÓN
        keyboard = [
            # ROW 1: Funciones básicas
            [
                InlineKeyboardButton("👤 Mi Perfil", callback_data="profile"),
                InlineKeyboardButton("🎯 Misiones", callback_data="missions"),
            ],
            # ROW 2: Entretenimiento
            [
                InlineKeyboardButton("🎮 Juegos", callback_data="games"),
                InlineKeyboardButton("🛍️ Tienda", callback_data="shop"),
            ],
            # ROW 3: CONVERSIÓN A VIP (DESTACADO)
            [
                InlineKeyboardButton(
                    "🔥 CONTENIDO PREMIUM 🔥", callback_data="premium_info"
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 ACCESO VIP - ¿Por qué Diana elige solo a algunos?",
                    callback_data="vip_info",
                )
            ],
            # ROW 4: Social proof
            [
                InlineKeyboardButton(
                    "💎 Testimonios VIP", callback_data="vip_testimonials"
                ),
                InlineKeyboardButton(
                    "🎭 ¿Cómo impresionar a Diana?", callback_data="how_to_vip"
                ),
            ],
            # ROW 5: Urgencia
            [
                InlineKeyboardButton(
                    "⚡ OFERTA ESPECIAL HOY", callback_data="special_offer"
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                intro_message, reply_markup=reply_markup, parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                intro_message, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def _show_vip_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
        intro_message: str = None,
    ) -> None:
        """Menú VIP - Enfocado en UPSELL de contenido premium"""

        if not intro_message:
            intro_message = f"""
{self.lucien.EMOJIS['diana']} **Diván Privado de Diana**

*[Con intimidad exclusiva]*

"*{user['first_name']}, mi querido miembro del círculo íntimo...*"

*[Con sonrisa seductora]*
"*¿Qué deseo tuyo puedo cumplir hoy?*"

{self.lucien.EMOJIS['lucien']} *[Con reverencia]*
Sus privilegios VIP le abren puertas especiales...
            """.strip()

        # MENÚ VIP ENFOCADO EN PREMIUM UPSELL
        keyboard = [
            # ROW 1: Funciones VIP avanzadas
            [
                InlineKeyboardButton("💎 Mi Perfil VIP", callback_data="profile_vip"),
                InlineKeyboardButton(
                    "🎯 Misiones Exclusivas", callback_data="vip_missions"
                ),
            ],
            # ROW 2: Entretenimiento exclusivo
            [
                InlineKeyboardButton("🎮 Juegos Íntimos", callback_data="vip_games"),
                InlineKeyboardButton("📊 Mi Progreso", callback_data="vip_progress"),
            ],
            # ROW 3: UPSELL PREMIUM (DESTACADO)
            [
                InlineKeyboardButton(
                    "🔥 SUBASTAS ULTRA EXCLUSIVAS 🔥", callback_data="premium_auctions"
                )
            ],
            [
                InlineKeyboardButton(
                    "✨ COLECCIÓN ÍNTIMA DE DIANA ✨",
                    callback_data="intimate_collection",
                )
            ],
            # ROW 4: Experiencias premium
            [
                InlineKeyboardButton(
                    "💋 Experiencias Personalizadas", callback_data="custom_experiences"
                ),
                InlineKeyboardButton(
                    "🎭 Contenido Solo Para Ti", callback_data="personal_content"
                ),
            ],
            # ROW 5: Ofertas especiales VIP
            [
                InlineKeyboardButton(
                    "⭐ OFERTAS SOLO PARA VIP ⭐", callback_data="vip_exclusive_offers"
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                intro_message, reply_markup=reply_markup, parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                intro_message, reply_markup=reply_markup, parse_mode="Markdown"
            )


# Registrar handlers
start_handler = CommandHandler("start", StartHandler().handle_start)
   
