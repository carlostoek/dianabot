
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class UserArchetype(Enum):
    EXPLORER = "explorer"      # Busca cada detalle
    DIRECT = "direct"          # Va al grano
    ROMANTIC = "romantic"      # Respuestas poéticas
    ANALYTICAL = "analytical"  # Busca comprensión intelectual
    PERSISTENT = "persistent"  # No se rinde fácilmente
    PATIENT = "patient"        # Toma tiempo para procesar
    UNDEFINED = "undefined"    # Aún no determinado

class InteractionPattern(Enum):
    IMMEDIATE = "immediate"           # Respuesta inmediata
    THOUGHTFUL = "thoughtful"         # Toma tiempo para responder
    RETURNING_QUICK = "returning_quick"  # Regresa rápido
    RETURNING_SLOW = "returning_slow"   # Regresa después de días
    FIRST_TIME = "first_time"         # Primera interacción

class LucienVoiceEnhanced:
    """Sistema de narrativa inmersiva con personalidad sarcástica y elegante"""

    def __init__(self):
        self.EMOJIS = {
            "lucien": "🍿",
            "diana": "🌸",
            "elegant": "✨",
            "sarcastic": "😝",
            "surprised": "🤔",
            "proud": "👑",
            "mysterious": "🔑",
            "warning": "⚠️",
            "success": "✅",
            "intimate": "💫",
            "exclusive": "🔮",
        }

    # === NIVEL 1 - ESCENA 1: BIENVENIDA DE DIANA ===

    def get_diana_level1_scene1_welcome(self, first_name: str, interaction_pattern: InteractionPattern, archetype: UserArchetype = UserArchetype.UNDEFINED) -> str:
        """Escena 1 - Bienvenida de Diana adaptada según comportamiento del usuario"""
        
        # Mensaje base de Diana
        base_message = f"""
{self.EMOJIS['diana']} *[Voz susurrante, como quien comparte un secreto]*

Bienvenido a Los Kinkys, {first_name}.

Has cruzado una línea que muchos ven... pero pocos realmente atraviesan.

Puedo sentir tu curiosidad desde aquí. Es... intrigante.  
No todos llegan con esa misma hambre en los ojos."""

        # Adaptación según patrón de interacción
        if interaction_pattern == InteractionPattern.IMMEDIATE:
            behavioral_note = f"""
*[Notando tu llegada inmediata]*

Veo que no perdiste tiempo en llegar hasta mí. Hay algo... urgente en tu energía que me resulta fascinante."""

        elif interaction_pattern == InteractionPattern.THOUGHTFUL:
            behavioral_note = f"""
*[Observando tu aproximación cuidadosa]*

Te tomaste tu tiempo para llegar aquí. Hay sabiduría en esa pausa... como si supieras que algunos encuentros requieren preparación mental."""

        elif interaction_pattern == InteractionPattern.RETURNING_QUICK:
            behavioral_note = f"""
*[Con sorpresa genuina]*

Oh... regresaste tan pronto. Hay algo en esa persistencia inmediata que me dice que algo en ti reconoce algo en mí."""

        elif interaction_pattern == InteractionPattern.RETURNING_SLOW:
            behavioral_note = f"""
*[Con una sonrisa conocedora]*

Volviste... después de procesar, después de reflexionar. Me pregunto qué conclusiones sacaste en el tiempo que estuviste lejos."""

        else:  # FIRST_TIME
            behavioral_note = f"""
*[Evaluando con intensidad]*

Este lugar responde a quienes saben que algunas puertas solo se abren desde adentro."""

        # Continuación del mensaje
        conclusion = f"""
Y yo... bueno, yo solo me revelo ante quienes comprenden que lo más valioso nunca se entrega fácilmente.

*[Pausa, como si estuviera evaluando al usuario]*

Algo me dice que tú podrías ser diferente.  
Pero eso... eso está por verse.

{self.EMOJIS['lucien']} *[Lucien aparece con elegancia]*

"*Oh, {first_name}... otro alma perdida que cree que puede entender a Diana. Qué... predecible.*"

*[Con sarcasmo elegante]*

"*Pero bueno, Diana insiste en darle una oportunidad a cada... esperanzado.*"
"""

        return f"{base_message}\n\n{behavioral_note}\n\n{conclusion}".strip()

    def get_lucien_level1_scene2_intro(self, first_name: str, user_archetype: UserArchetype = UserArchetype.UNDEFINED) -> str:
        """Escena 2 - Lucien presenta el primer desafío"""
        
        base_message = f"""
{self.EMOJIS['lucien']} *[Con aire de superioridad elegante]*

Ah, otro visitante de Diana... {first_name}.  
Permíteme presentarme: Lucien, guardián de los secretos que ella no cuenta... todavía.

*[Observando con aire analítico]*

Veo que Diana ya plantó esa semilla de curiosidad en ti. Lo noto en cómo llegaste hasta aquí.  
Pero la curiosidad sin acción es solo... voyeurismo pasivo."""

        # Adaptación según arquetipo (si ya se detectó)
        if user_archetype == UserArchetype.EXPLORER:
            archetype_note = f"""
*[Con interés genuino]*

Noto que examinas cada detalle... Interesante. Diana aprecia a quienes ven más allá de lo obvio."""

        elif user_archetype == UserArchetype.DIRECT:
            archetype_note = f"""
*[Con aprobación reluctante]*

Sin rodeos, directo al grano. Diana encuentra refrescante esa honestidad sin filtros."""

        elif user_archetype == UserArchetype.ROMANTIC:
            archetype_note = f"""
*[Con una sonrisa barely perceptible]*

Hay una poesía en cómo te aproximas a esto. Diana tiene debilidad por las almas... artísticas."""

        else:
            archetype_note = f"""
*[Con evaluación continua]*

Aún estoy... catalogándote. Diana observa. Siempre observa."""

        conclusion = f"""
Y lo que más le fascina no es la obediencia ciega, sino la *intención* detrás de cada gesto.

*[Con desafío sutil]*

**Tu primera prueba es simple:** Reacciona al último mensaje del canal.  
Pero hazlo porque realmente quieres entender, no porque se te ordena.

*[Con aire conspiratorio]*

Diana sabrá la diferencia. Siempre sabe."""

        return f"{base_message}\n\n{archetype_note}\n\n{conclusion}".strip()

    def get_diana_reaction_response(self, reaction_time: str, first_name: str) -> Dict[str, str]:
        """Respuestas de Diana según el tiempo de reacción del usuario"""
        
        if reaction_time == "immediate":
            return {
                "diana_message": f"""
{self.EMOJIS['diana']} *[Con una sonrisa apenas perceptible]*

{first_name}... reaccionaste sin dudar.

*[Con aprobación sutil]*

Hay algo hermoso en esa espontaneidad. No todos tienen el coraje de actuar cuando sienten que algo es correcto.

*[Acercándose ligeramente]*

Impulsivo... pero no imprudente. Hay una diferencia que pocos entienden.  
Me gusta eso de ti.""",
                
                "lucien_comment": f"""
{self.EMOJIS['lucien']} *[Con sorpresa fingida]*

"*Bueno, bueno... parece que {first_name} no es completamente... inútil.*"

*[Con eficiencia profesional]*

"*Tu Mochila del Viajero está lista. Diana eligió algo específico para alguien como tú: alguien que actúa when it feels right.*"
""",
                "reward_type": "immediate_action_reward"
            }
        
        elif reaction_time == "thoughtful":
            return {
                "diana_message": f"""
{self.EMOJIS['diana']} *[Con mirada pensativa]*

{first_name}... te tomaste tu tiempo.

*[Con apreciación profunda]*

Observaste, evaluaste, consideraste. Hay sabiduría en esa paciencia que encuentro... seductora.

*[Con intensidad creciente]*

Me fascina cómo algunos saben que lo genuino no debe apresurarse.  
Tu manera de aproximarte dice más de ti que cualquier reacción impulsiva.""",
                
                "lucien_comment": f"""
{self.EMOJIS['lucien']} *[Con aprobación reluctante]*

"*Hmm... {first_name} comprende que las mejores decisiones no se toman a la ligera. Qué... raro.*"

*[Con aire místico]*

"*Tu Mochila del Viajero contiene algo especial, seleccionado para alguien que sabe esperar el momento correcto.*"
""",
                "reward_type": "thoughtful_action_reward"
            }
        
        else:  # no_reaction
            return {
                "diana_message": f"""
{self.EMOJIS['diana']} *[Con decepción sutil pero comprensiva]*

{first_name}... decidiste no reaccionar.

*[Con aire reflexivo]*

Interesante. A veces la acción más reveladora es... la inacción.  
Quizás necesitas más tiempo para decidir si realmente quieres este viaje.

*[Con paciencia enigmática]*

Estaré aquí cuando estés listo.""",
                
                "lucien_comment": f"""
{self.EMOJIS['lucien']} *[Con sarcasmo palpable]*

"*Ah, qué sorpresa... otro que se queda paralizado ante el primer desafío.*"

*[Con desdén elegante]*

"*Diana es paciente, yo... menos. Pero bueno, siempre puedes intentar de nuevo when you grow a spine.*"
""",
                "reward_type": "no_action_consequence"
            }

    # === MÉTODOS DE ANÁLISIS DE COMPORTAMIENTO ===

    def analyze_interaction_pattern(self, user_data: Dict) -> InteractionPattern:
        """Analiza el patrón de interacción del usuario"""
        
        # Esta lógica se basaría en datos reales del usuario
        # Por ahora simulamos con lógica básica
        
        last_activity = user_data.get('last_activity')
        created_today = user_data.get('created_today', True)
        previous_sessions = user_data.get('session_count', 0)
        
        if created_today and previous_sessions == 0:
            return InteractionPattern.FIRST_TIME
        elif previous_sessions > 0:
            # Lógica para determinar si regresa rápido o lento
            # basada en tiempo desde última actividad
            return InteractionPattern.RETURNING_QUICK  # Simplificado
        else:
            return InteractionPattern.IMMEDIATE

    def detect_user_archetype(self, interaction_history: List[Dict]) -> UserArchetype:
        """Detecta el arquetipo del usuario basado en su historial"""
        
        # Análisis simplificado - en implementación real sería más sofisticado
        if not interaction_history:
            return UserArchetype.UNDEFINED
            
        # Aquí iría lógica de ML o análisis de patrones
        # Por ahora retornamos aleatorio para testing
        return UserArchetype.EXPLORER

    # === MÉTODOS AUXILIARES ===

    def get_reward_content(self, reward_type: str, user_archetype: UserArchetype) -> Dict[str, str]:
        """Genera contenido de recompensa personalizado"""
        
        rewards = {
            "immediate_action_reward": {
                "title": "🎒 Mochila del Viajero Impulsivo",
                "description": "Para quienes actúan con el corazón",
                "content": "Primera pista del mapa + Acceso a chat especial",
                "rarity": "Común pero personalizado"
            },
            "thoughtful_action_reward": {
                "title": "🎒 Mochila del Viajero Reflexivo", 
                "description": "Para quienes piensan antes de actuar",
                "content": "Primera pista del mapa + Acceso a análisis profundo",
                "rarity": "Común pero personalizado"
            },
            "no_action_consequence": {
                "title": "⏳ Oportunidad Perdida",
                "description": "Las dudas tienen consecuencias",
                "content": "Chance de redemption en 24 horas",
                "rarity": "Lesson learned"
            }
        }
        
        return rewards.get(reward_type, rewards["no_action_consequence"])

    # === MENSAJES DE ERROR CON PERSONALIDAD ===

    def get_error_message(self, context: str = "") -> str:
        """Mensaje de error con el tono sarcástico de Lucien"""
        
        error_messages = [
            f"{self.EMOJIS['lucien']} *[Con exasperación elegante]*\n\n\"*Oh, qué sorpresa... algo se rompió. Como si no fuera suficientemente difícil mantener todo funcionando without your help.*\"\n\n*[Con aire profesional forzado]*\n\n\"*Por favor, intenta con /start de nuevo y... maybe this time be more careful.*\"",
            
            f"{self.EMOJIS['lucien']} *[Suspirando dramáticamente]*\n\n\"*Error técnico. Qué elegante timing, just when things were getting interesting.*\"\n\n*[Con desdén fingido]*\n\n\"*Diana me pide que te asegure que esto se resolverá. I personally make no such promises.*\"",
        ]
        
        return random.choice(error_messages)

