from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from services.user_service import UserService
from services.narrative_service import NarrativeService
from utils.keyboards import create_start_keyboard

class StartHandler:
    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.narrative_service = NarrativeService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        self.router.message.register(self.handle_start, CommandStart())

    async def handle_start(self, message: Message, user: dict):
        """Manejar comando /start"""
        user_obj = user  # Ya viene del middleware
        
        # Determinar si es usuario nuevo
        is_new_user = user_obj.narrative_level == 1 and not user_obj.narrative_state
        
        if is_new_user:
            await self._handle_new_user(message, user_obj)
        else:
            await self._handle_returning_user(message, user_obj)

    async def _handle_new_user(self, message: Message, user):
        """Manejar usuario nuevo"""
        # Obtener primera escena narrativa
        scene_content = await self.narrative_service.get_scene_content(1, 1, user.id)
        
        welcome_text = f"""🎭 *¡Bienvenido a DianaBot, {user.first_name}!*

{scene_content['content']}

💰 **Has recibido 100 besitos de bienvenida**
🎯 **Nivel:** {user.level}
📚 **Narrativa:** Nivel {user.narrative_level}"""

        keyboard = create_start_keyboard(user, is_new=True)
        
        await message.answer(
            welcome_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def _handle_returning_user(self, message: Message, user):
        """Manejar usuario recurrente"""
        # Personalizar mensaje según progreso
        narrative_state = await self.narrative_service.get_user_narrative_state(user.id)
        
        welcome_text = f"""🎭 *¡{user.first_name}, has regresado!*

*Lucien sonríe con complicidad...*

"Ah, un visitante familiar. Diana me comentó que has estado progresando..."

📊 **Tu progreso actual:**
• Nivel: {user.level}
• Besitos: {user.besitos}
• Narrativa: Nivel {user.narrative_level}
• Estado: {'👑 VIP' if user.is_vip else '🌟 Free'}

¿Qué deseas hacer hoy?"""

        keyboard = create_start_keyboard(user, is_new=False)
        
        await message.answer(
            welcome_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
      )
      
