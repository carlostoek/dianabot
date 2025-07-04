from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class StartHandler:
    def __init__(self):
        self.router = Router()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        self.router.message.register(self.handle_start, CommandStart())

    async def handle_start(self, message: Message):
        """Manejar comando /start"""
        try:
            user_name = message.from_user.first_name or "Usuario"
            
            welcome_text = f"""🎭 *¡Bienvenido a DianaBot, {user_name}!*

*Diana aparece entre las sombras...*

"Bienvenido a Los Kinkys. Has cruzado una línea que muchos ven... pero pocos realmente atraviesan.

Puedo sentir tu curiosidad desde aquí. Es... intrigante."

💰 **Has recibido 100 besitos de bienvenida**
🎯 **Nivel:** 1
📚 **Narrativa:** Nivel 1

¿Estás listo para descubrir más?"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🚪 Descubrir más", callback_data="discover_more")],
                [InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile")],
                [InlineKeyboardButton("🎮 Explorar", callback_data="explore")]
            ])
            
            await message.answer(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"Error en start_handler: {e}")
            await message.answer(
                "¡Hola! Bienvenido a DianaBot. El sistema está iniciando...",
                parse_mode="Markdown"
            )
            
