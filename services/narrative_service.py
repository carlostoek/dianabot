from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import User, NarrativeState, StoryScene
from config.database import get_db
from typing import Dict, List, Optional
import json

class NarrativeService:
    
    # Narrative content based on the provided script
    NARRATIVE_CONTENT = {
        1: {  # Nivel 1 - Los Kinkys
            1: {  # Escena 1 - Bienvenida de Diana
                "character": "diana",
                "content": """🌸 **Diana:**
*[Voz susurrante, como quien comparte un secreto]*

Bienvenido a Los Kinkys.  
Has cruzado una línea que muchos ven... pero pocos realmente atraviesan.

Puedo sentir tu curiosidad desde aquí. Es... intrigante.  
No todos llegan con esa misma hambre en los ojos.

Este lugar responde a quienes saben que algunas puertas solo se abren desde adentro.  
Y yo... bueno, yo solo me revelo ante quienes comprenden que lo más valioso nunca se entrega fácilmente.

*[Pausa, como si estuviera evaluando al usuario]*

Algo me dice que tú podrías ser diferente.  
Pero eso... eso está por verse.""",
                "buttons": [{"text": "🚪 Descubrir más", "callback": "narrative_1_2"}],
                "rewards": {"besitos": 25, "xp": 50}
            },
            2: {  # Escena 2 - Lucien y el Primer Desafío
                "character": "lucien",
                "content": """🎩 **Lucien:**
Ah, otro visitante de Diana.  
Permíteme presentarme: Lucien, guardián de los secretos que ella no cuenta... todavía.

Veo que Diana ya plantó esa semilla de curiosidad en ti. Lo noto en cómo llegaste hasta aquí.  
Pero la curiosidad sin acción es solo... voyeurismo pasivo.

Diana observa. Siempre observa.  
Y lo que más le fascina no es la obediencia ciega, sino la intención detrás de cada gesto.

**Misión:** Reacciona al último mensaje del canal. Pero hazlo porque realmente quieres entender, no porque se te ordena.""",
                "buttons": [{"text": "✅ Entendido", "callback": "narrative_1_mission_1"}],
                "mission": {
                    "type": "channel_reaction",
                    "description": "Reaccionar al último mensaje del canal",
                    "reward_besitos": 50,
                    "reward_xp": 75
                }
            }
        },
        2: {  # Nivel 2 - Los Kinkys Profundización
            1: {
                "character": "diana",
                "content": """🌸 **Diana:**
*[Con una sonrisa conocedora]*

Volviste. Interesante...  
No todos regresan después de la primera revelación. Algunos se quedan satisfechos con las migajas de misterio.

*[Pausa evaluativa]*

Pero tú... tú quieres más. Puedo sentir esa hambre desde aquí.  
Hay algo delicioso en esa persistencia tuya.""",
                "buttons": [{"text": "🔍 Explorar más profundo", "callback": "narrative_2_2"}],
                "rewards": {"besitos": 30, "xp": 60}
            }
        },
        4: {  # Nivel 4 - El Diván
            1: {
                "character": "diana",
                "content": """🌸 **Diana:**
*[Con una sonrisa genuina, pero manteniendo la distancia]*

Oh... finalmente decidiste cruzar completamente.  
Bienvenido al Diván, donde las máscaras se vuelven innecesarias... casi.

Puedo sentir cómo has cambiado desde Los Kinkys. Hay algo diferente en tu energía.  
Algo que me dice que empiezas a comprender no solo lo que busco... sino por qué lo busco.""",
                "buttons": [{"text": "🚪 Adentrarse en el Diván", "callback": "narrative_4_2"}],
                                "rewards": {"besitos": 100, "xp": 200},
                "vip_required": True
            }
        }
    }

    async def get_user_narrative_state(self, user_id: int) -> dict:
        """Obtener estado narrativo actual del usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                return {
                    "level": user.narrative_level,
                    "state": user.narrative_state or {},
                    "archetype": user.user_archetype
                }
            return {"level": 1, "state": {}, "archetype": None}

    async def get_scene_content(self, level: int, scene: int, user_id: int) -> dict:
        """Obtener contenido de escena personalizado"""
        base_content = self.NARRATIVE_CONTENT.get(level, {}).get(scene, {})
        
        if not base_content:
            return None
        
        # Personalizar contenido basado en arquetipo del usuario
        user_state = await self.get_user_narrative_state(user_id)
        archetype = user_state.get("archetype")
        
        content = base_content.copy()
        
        # Personalización por arquetipo
        if archetype:
            content = await self._personalize_content(content, archetype, user_id)
        
        return content

    async def _personalize_content(self, content: dict, archetype: str, user_id: int) -> dict:
        """Personalizar contenido según arquetipo del usuario"""
        personalizations = {
            "explorer": {
                "diana_suffix": "\n\n*Diana nota tu naturaleza exploradora*\nVeo cómo examinas cada detalle. Esa atención me resulta... cautivadora.",
                "lucien_suffix": "\n\nTu manera meticulosa de observar no pasa desapercibida."
            },
            "direct": {
                "diana_suffix": "\n\n*Diana aprecia tu franqueza*\nMe gusta esa honestidad directa tuya. Tan pocos se atreven a ser auténticos.",
                "lucien_suffix": "\n\nTu aproximación directa es refrescante en un mundo de subterfugios."
            },
            "romantic": {
                "diana_suffix": "\n\n*Diana sonríe ante tu sensibilidad*\nHay una poesía en tu manera de ver las cosas que me conmueve.",
                "lucien_suffix": "\n\nTu alma romántica comprende matices que otros pasan por alto."
            }
        }
        
        if archetype in personalizations:
            character = content.get("character", "")
            suffix_key = f"{character}_suffix"
            if suffix_key in personalizations[archetype]:
                content["content"] += personalizations[archetype][suffix_key]
        
        return content

    async def advance_narrative(self, user_id: int, scene_data: dict) -> dict:
        """Avanzar narrativa del usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                # Create narrative state record
                narrative_state = NarrativeState(
                    user_id=user_id,
                    level=scene_data.get("level"),
                    scene=scene_data.get("scene"),
                    state_data=scene_data.get("state_data", {})
                )
                db.add(narrative_state)
                
                # Update user narrative progress
                if scene_data.get("level") > user.narrative_level:
                    user.narrative_level = scene_data.get("level")
                
                # Update user state
                current_state = user.narrative_state or {}
                current_state.update(scene_data.get("state_data", {}))
                user.narrative_state = current_state
                
                await db.commit()
                return {"success": True}
            return {"success": False}

    async def detect_user_archetype(self, user_id: int, interaction_data: dict) -> str:
        """Detectar arquetipo del usuario basado en interacciones"""
        # Análisis de patrones de comportamiento
        response_time = interaction_data.get("response_time", 0)
        interaction_type = interaction_data.get("type", "")
        content_length = interaction_data.get("content_length", 0)
        
        # Lógica de detección de arquetipo
        if response_time < 5:  # Respuesta rápida
            if content_length > 100:
                return "direct"
            else:
                return "impulsive"
        elif response_time > 30:  # Respuesta reflexiva
            if content_length > 150:
                return "analytical"
            else:
                return "patient"
        else:
            if "emotion" in interaction_type:
                return "romantic"
            else:
                return "explorer"

    async def create_trivia_question(self, level: int, user_id: int) -> dict:
        """Crear pregunta de trivia narrativa contextual"""
        trivia_questions = {
            1: [
                {
                    "question": "¿Cuál es la primera impresión que Diana menciona sobre ti?",
                    "options": ["Tu obediencia", "Tu curiosidad", "Tu belleza", "Tu dinero"],
                    "correct": 1,
                    "explanation": "Diana nota específicamente 'esa hambre en los ojos' y tu curiosidad.",
                    "reward_besitos": 25,
                    "reward_xp": 50
                },
                {
                    "question": "Según Lucien, ¿qué fascina más a Diana?",
                    "options": ["La obediencia ciega", "La intención detrás de cada gesto", "Los regalos costosos", "Las palabras bonitas"],
                    "correct": 1,
                    "explanation": "Lucien explica que Diana observa la intención, no solo las acciones.",
                    "reward_besitos": 30,
                    "reward_xp": 60
                }
            ],
            4: [
                {
                    "question": "¿Qué representa el Diván según Diana?",
                    "options": ["Un lugar físico", "Donde las máscaras se vuelven innecesarias", "Un canal premium", "Su habitación"],
                    "correct": 1,
                    "explanation": "Diana describe el Diván como el lugar donde las máscaras se vuelven innecesarias... casi.",
                    "reward_besitos": 50,
                    "reward_xp": 100
                }
            ]
        }
        
        questions = trivia_questions.get(level, [])
        if questions:
            import random
            return random.choice(questions)
        return None

    async def process_trivia_answer(self, user_id: int, question_id: str, answer: int) -> dict:
        """Procesar respuesta de trivia narrativa"""
        # Aquí iría la lógica para validar respuesta y otorgar recompensas
        # Por simplicidad, retornamos un resultado de ejemplo
        return {
            "correct": True,
            "explanation": "¡Correcto! Has demostrado comprensión narrativa.",
            "rewards": {"besitos": 25, "xp": 50}
        }

    async def get_available_scenes(self, user_id: int) -> List[dict]:
        """Obtener escenas disponibles para el usuario"""
        user_state = await self.get_user_narrative_state(user_id)
        current_level = user_state["level"]
        
        available_scenes = []
        
        # Obtener escenas del nivel actual
        level_scenes = self.NARRATIVE_CONTENT.get(current_level, {})
        for scene_num, scene_data in level_scenes.items():
            available_scenes.append({
                "level": current_level,
                "scene": scene_num,
                "title": f"Nivel {current_level} - Escena {scene_num}",
                "character": scene_data.get("character"),
                "vip_required": scene_data.get("vip_required", False)
            })
        
        return available_scenes

    async def unlock_next_level(self, user_id: int) -> bool:
        """Desbloquear siguiente nivel narrativo"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user and user.narrative_level < 6:
                user.narrative_level += 1
                await db.commit()
                
                # Reward for level unlock
                from services.user_service import UserService
                user_service = UserService()
                await user_service.add_besitos(
                    user_id, 
                    user.narrative_level * 50, 
                    f"Desbloqueo Nivel Narrativo {user.narrative_level}"
                )
                
                return True
            return False
            
