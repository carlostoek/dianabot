from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from services.narrative_service import NarrativeService
from services.user_service import UserService
from utils.keyboards import create_narrative_keyboard, create_trivia_keyboard

class NarrativeHandlers:
    def __init__(self):
        self.router = Router()
        self.narrative_service = NarrativeService()
        self.user_service = UserService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        
        # Callbacks narrativos
        self.router.callback_query.register(
            self.handle_narrative_scene, 
            F.data.startswith("narrative_")
        )
        self.router.callback_query.register(
            self.handle_trivia_answer,
            F.data.startswith("trivia_answer_")
        )
        self.router.callback_query.register(
            self.handle_scene_progression,
            F.data.startswith("scene_")
        )

    async def handle_narrative_scene(self, callback: CallbackQuery, user: dict):
        """Manejar progresión de escenas narrativas"""
        await callback.answer()
        
        # Extraer nivel y escena del callback_data
        # Formato: narrative_level_scene
        parts = callback.data.split("_")
        if len(parts) >= 3:
            level = int(parts[1])
            scene = int(parts[2])
        else:
            level, scene = 1, 1
        
        # Verificar permisos VIP para niveles 4+
        if level >= 4 and not user.is_vip:
            await callback.message.edit_text(
                "🏛️ *Acceso Restringido*\n\n"
                "Esta parte de la narrativa está disponible solo en el Diván (Canal VIP).\n\n"
                "💎 *¿Listo para cruzar completamente hacia Diana?*",
                reply_markup=create_narrative_keyboard("vip_promotion"),
                parse_mode="Markdown"
            )
            return
        
        # Obtener contenido de la escena
        scene_content = await self.narrative_service.get_scene_content(level, scene, user.id)
        
        if not scene_content:
            await callback.message.edit_text(
                "❌ Escena no encontrada. Contacta al administrador.",
                parse_mode="Markdown"
            )
            return
        
        # Procesar recompensas si las hay
        if "rewards" in scene_content:
            rewards = scene_content["rewards"]
            if "besitos" in rewards:
                await self.user_service.add_besitos(
                    user.id, rewards["besitos"], 
                    f"Escena narrativa {level}-{scene}"
                )
            if "xp" in rewards:
                await self.user_service.add_experience(user.id, rewards["xp"])
        
        # Preparar texto con personalización
        content_text = scene_content["content"]
        
        # Agregar información de recompensas
        if "rewards" in scene_content:
            rewards = scene_content["rewards"]
            reward_text = "\n\n✨ *Recompensas obtenidas:*\n"
            if "besitos" in rewards:
                reward_text += f"💰 +{rewards['besitos']} besitos\n"
            if "xp" in rewards:
                reward_text += f"⭐ +{rewards['xp']} XP\n"
            content_text += reward_text
        
        # Crear teclado según botones definidos
        keyboard = create_narrative_keyboard(scene_content.get("buttons", []))
        
        await callback.message.edit_text(
            content_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Registrar progreso narrativo
        await self.narrative_service.advance_narrative(user.id, {
            "level": level,
            "scene": scene,
            "state_data": {"completed_at": str(callback.message.date)}
        })

    async def handle_trivia_answer(self, callback: CallbackQuery, user: dict):
        """Manejar respuestas de trivia narrativa"""
        await callback.answer()
        
        # Extraer datos de la respuesta
        # Formato: trivia_answer_questionId_answerIndex
        parts = callback.data.split("_")
        question_id = parts[2]
        answer_index = int(parts[3])
        
        # Procesar respuesta
        result = await self.narrative_service.process_trivia_answer(
            user.id, question_id, answer_index
        )
        
        if result["correct"]:
            response_text = f"""🎉 *¡Respuesta Correcta!*

{result['explanation']}

✨ **Recompensas:**
💰 +{result['rewards']['besitos']} besitos
⭐ +{result['rewards']['xp']} XP"""
            
            # Otorgar recompensas
            await self.user_service.add_besitos(
                user.id, result['rewards']['besitos'], "Trivia narrativa correcta"
            )
            await self.user_service.add_experience(user.id, result['rewards']['xp'])
        else:
            response_text = f"""❌ *Respuesta Incorrecta*

{result.get('explanation', 'Inténtalo de nuevo.')}

💡 *Consejo:* Presta más atención a los detalles de la narrativa."""
        
        keyboard = create_narrative_keyboard([
            {"text": "🧠 Nueva Trivia", "callback": "trivia_new"},
            {"text": "📖 Continuar Historia", "callback": "narrative_continue"}
        ])
        
        await callback.message.edit_text(
            response_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def handle_scene_progression(self, callback: CallbackQuery, user: dict):
        """Manejar progresión entre escenas"""
        await callback.answer()
        
        action = callback.data
        
        if action == "scene_next":
            # Avanzar a siguiente escena disponible
            current_state = await self.narrative_service.get_user_narrative_state(user.id)
            next_level = current_state["level"]
            next_scene = 1  # Determinar siguiente escena lógicamente
            
            await self.handle_narrative_scene(callback, user)
        
        elif action == "scene_menu":
            # Mostrar menú de escenas disponibles
            available_scenes = await self.narrative_service.get_available_scenes(user.id)
            
            menu_text = "📚 *Escenas Disponibles*\n\n"
            buttons = []
            
            for scene in available_scenes:
                if scene["vip_required"] and not user.is_vip:
                    continue
                
                scene_title = f"Nivel {scene['level']} - Escena {scene['scene']}"
                menu_text += f"• {scene_title} ({scene['character'].title()})\n"
                
                buttons.append({
                    "text": scene_title,
                    "callback": f"narrative_{scene['level']}_{scene['scene']}"
                })
            
            keyboard = create_narrative_keyboard(buttons)
            
            await callback.message.edit_text(
                menu_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
              )
          
