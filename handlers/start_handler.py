from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.user_service import UserService
from services.mission_service import MissionService
from services.game_service import GameService
from services.auction_service import AuctionService
from services.shop_service import ShopService
from utils.lucien_voice import LucienVoice
from handlers.start_handler import StartHandler
from typing import Dict, Any


class CallbackHandler:
    """Maneja todos los callbacks de botones con experiencia SEDUCTORA"""

    def __init__(self):
        self.user_service = UserService()
        self.mission_service = MissionService()
        self.game_service = GameService()
        self.auction_service = AuctionService()
        self.shop_service = ShopService()
        self.lucien = LucienVoice()
        self.start_handler = StartHandler()

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Router principal de callbacks"""

        query = update.callback_query
        await query.answer()

        user_data = {
            "telegram_id": query.from_user.id,
            "username": query.from_user.username,
            "first_name": query.from_user.first_name,
            "last_name": query.from_user.last_name,
        }

        user = self.user_service.get_or_create_user(user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user.telegram_id)

        # Router de callbacks
        callback_data = query.data

        # === INTRO CALLBACKS ===
        if callback_data == "intro_diana":
            await self._show_diana_intro(update, context, user)
        elif callback_data == "intro_lucien":
            await self._show_lucien_intro(update, context, user)
        elif callback_data == "intro_bot":
            await self._show_bot_intro(update, context, user)

        # === NAVIGATION ===
        elif callback_data == "main_menu":
            await self.start_handler._show_main_menu(
                update, context, user, narrative_state
            )
        elif callback_data == "back":
            await self._handle_back(update, context, user, narrative_state)

        # === PROFILE ===
        elif callback_data == "profile":
            await self._show_profile(update, context, user, narrative_state)

        # === CONVERSION FOCUSED ===
        elif callback_data == "premium_info":
            await self._show_premium_info(update, context, user)
        elif callback_data == "vip_info":
            await self._show_vip_info(update, context, user)
        elif callback_data == "vip_testimonials":
            await self._show_vip_testimonials(update, context, user)
        elif callback_data == "how_to_vip":
            await self._show_how_to_vip(update, context, user)
        elif callback_data == "special_offer":
            await self._show_special_offer(update, context, user)

        # === VIP UPSELLS ===
        elif callback_data == "intimate_collection":
            await self._show_intimate_collection(update, context, user)
        elif callback_data == "custom_experiences":
            await self._show_custom_experiences(update, context, user)
        elif callback_data == "vip_exclusive_offers":
            await self._show_vip_exclusive_offers(update, context, user)

        # === FUNCTIONALITY ===
        elif callback_data == "missions":
            await self._show_missions(update, context, user, narrative_state)
        elif callback_data == "games":
            await self._show_games(update, context, user)

        # Agregar más handlers según necesidad...

    async def _show_bot_intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict) -> None:
        """Presentación breve del bot"""
        bot_intro = f"""
{self.lucien.EMOJIS['lucien']} *[Con tono amable]*

{user['first_name']}, bienvenido a este universo interactivo.

Aquí, cada elección que haces influye en la historia.

{self.lucien.EMOJIS['diana']} *Diana observa atentamente...* 
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            bot_intro, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, narrative_state: Any) -> None:
        """Regresa al menú principal"""
        await self.start_handler._show_main_menu(update, context, user, narrative_state)
