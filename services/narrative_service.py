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
