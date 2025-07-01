
    from typing import Dict, Any, Optional, List
from models.narrative_state import (
    UserNarrativeState,
    NarrativeLevel,
    UserArchetype,
    EmotionalResponse,
)
from models.user import User
from datetime import datetime, timedelta
import random


class LucienVoice:
    """Sistema centralizado para la voz y personalidad de Lucien"""

    def __init__(self):
        self.EMOJIS = {
            "lucien": "🎩",
            "diana": "🌸",
            "elegant": "✨",
            "sarcastic": "😏",
            "surprised": "🤔",
            "proud": "👑",
            "mysterious": "🗝️",
            "warning": "⚠️",
            "success": "✅",
            "intimate": "💫",
            "exclusive": "🔮",
        }

    # ===== MENSAJES DE BIENVENIDA Y NAVEGACIÓN =====

    def welcome_message(self, user: User, narrative_state: UserNarrativeState) -> str:
        """Mensaje de bienvenida personalizado según el progreso narrativo"""

        if narrative_state.current_level == NarrativeLevel.NEWCOMER:
            return f"""
{self.EMOJIS['lucien']} **Bienvenido, {user.first_name}**

Ah, un rostro nuevo. Permíteme presentarme con la elegancia que la situación merece: **Lucien**, mayordomo digital y guardián de los secretos que Diana no cuenta... *todavía*.

{self.EMOJIS['mysterious']} Diana me ha encargado evaluar a quienes llegan hasta aquí. No todos comprenden que algunas puertas solo se abren desde adentro.

**¿Estás listo para comenzar tu viaje hacia ella?**

*[Con una sonrisa enigmática]*
Por cierto, Diana ya sabe que estás aquí. Está... observando.
            """.strip()

        elif narrative_state.current_level in [
            NarrativeLevel.LEVEL_1_KINKY,
            NarrativeLevel.LEVEL_2_KINKY_DEEP,
        ]:
            return f"""
{self.EMOJIS['lucien']} **Ah, {user.first_name} regresa**

*[Ajustándose los guantes con aire de satisfacción]*

Diana mencionó que podrías volver. Hay algo en tu persistencia que encuentra... intrigante.

{self._get_archetype_recognition(narrative_state.primary_archetype)}

**Tu progreso hasta ahora:** {self._format_narrative_progress(narrative_state)}

¿Listo para continuar donde lo dejamos?
            """.strip()

        elif narrative_state.has_divan_access:
            return f"""
{self.EMOJIS['lucien']} **Bienvenido de vuelta al Diván, {user.first_name}**

*[Con respeto genuino teñido de ironía]*

Mira quién ha llegado al círculo íntimo. Diana está {self._get_diana_mood(narrative_state)} y ha estado esperando tu regreso.

{self.EMOJIS['intimate']} **Tu nivel de comprensión:** {narrative_state.diana_trust_level}/100
{self.EMOJIS['exclusive']} **Secretos compartidos:** {len(narrative_state.special_recognitions)}

*[Susurrando conspiradoramente]*
Entre tú y yo, creo que eres uno de los pocos que realmente la *entiende*.
            """.strip()

        return self._generic_welcome(user)

    def main_menu_message(self, user: User, narrative_state: UserNarrativeState) -> str:
        """Mensaje del menú principal con voz de Lucien"""

        base_message = f"""
{self.EMOJIS['lucien']} **Panel de Actividades - {user.first_name}**

*[Consultando su elegante reloj de bolsillo]*

Diana está {self._get_diana_current_state(narrative_state)} y me ha encargado que te ofrezca las siguientes... oportunidades.

{self._get_personalized_menu_intro(narrative_state)}
        """.strip()

        return base_message

    # ===== MENSAJES DE MISIONES =====

    def missions_intro(
        self,
        user: User,
        active_missions_count: int,
        narrative_state: UserNarrativeState,
    ) -> str:
        """Introducción a las misiones con contexto narrativo"""

        if active_missions_count == 0:
            return f"""
{self.EMOJIS['lucien']} **Misiones de Proximidad**

*[Con aire ligeramente aburrido]*

Ah, qué sorpresa. No tienes misiones activas. Diana debe estar... reconsiderando su nivel de interés en ti.

{self._get_mission_encouragement_by_archetype(narrative_state.primary_archetype)}

*[Mirándote con evaluación divertida]*
Pero no te preocupes. Diana siempre da segundas oportunidades... a quienes demuestran que las merecen.
            """.strip()

        else:
            return f"""
{self.EMOJIS['lucien']} **Tus Misiones Actuales**

*[Con aprobación apenas disimulada]*

Diana te ha asignado **{active_missions_count}** misiones. Cada una es una oportunidad de demostrar que comprendes... sus expectativas.

{self._get_mission_context_by_level(narrative_state.current_level)}

*[Con humor seco]*
Recuerda: Diana observa no solo *si* completas las misiones, sino *cómo* las completas.
            """.strip()

    def mission_completed_celebration(
        self, mission_title: str, rewards: Dict, narrative_state: UserNarrativeState
    ) -> str:
        """Celebración de misión completada"""

        base_celebration = f"""
{self.EMOJIS['lucien']} **Misión Completada con Elegancia**

*[Con satisfacción visible]*

**"{mission_title}"** - Completada con el estilo que Diana esperaba.

{self._get_completion_style_comment(narrative_state)}

**Recompensas recibidas:**
💋 **{rewards.get('besitos', 0)} Besitos** - Tokens de aprecio de Diana
⚡ **{rewards.get('experience', 0)} Experiencia** - Crecimiento personal
        """.strip()

        # Añadir comentario especial de Diana si el nivel es alto
        if narrative_state.diana_interest_level > 70:
            base_celebration += f"""

{self.EMOJIS['diana']} *Diana susurra desde las sombras:*
"*{self._get_diana_completion_whisper(narrative_state)}*"
            """.strip()

        return base_celebration

    # ===== MENSAJES DE JUEGOS =====

    def games_intro(self, user: User, narrative_state: UserNarrativeState) -> str:
        """Introducción a los juegos como entretenimiento que Diana observa"""

        return f"""
{self.EMOJIS['lucien']} **Entretenimientos para Diana**

*[Con sonrisa enigmática]*

Diana encuentra... educativo observar cómo las personas enfrentan desafíos. Cada juego es una ventana a tu personalidad que ella estudia con fascinación.

{self._get_game_context_by_archetype(narrative_state.primary_archetype)}

*[Ajustándose la corbata]*
¿Prefieres demostrar tu intelecto, tu intuición, o tu persistencia? Diana está observando...
        """.strip()

    def game_result_commentary(
        self,
        game_type: str,
        score: int,
        performance: str,
        narrative_state: UserNarrativeState,
    ) -> str:
        """Comentario de Lucien sobre los resultados del juego"""

        base_commentary = f"""
{self.EMOJIS['lucien']} **Análisis del Rendimiento**

*[Tomando notas mentales]*

{self._get_performance_analysis(game_type, score, performance)}

{self._get_diana_observation_comment(score, narrative_state)}
        """.strip()

        return base_commentary

    # ===== MENSAJES DE SUBASTAS =====

    def auction_intro(self, user: User, narrative_state: UserNarrativeState) -> str:
        """Introducción a las subastas como oportunidades de impresionar"""

        if not narrative_state.has_divan_access:
            return f"""
{self.EMOJIS['lucien']} **Subastas de Proximidad**

*[Con aire de exclusividad]*

Las subastas son donde Diana observa quién está verdaderamente comprometido con acercarse a ella. No se trata solo de besitos, se trata de... dedicación.

{self._get_auction_eligibility_message(narrative_state)}

*[Con una sonrisa mordaz]*
Diana nota quién participa y quién solo observa desde la distancia.
            """.strip()
        else:
            return f"""
{self.EMOJIS['lucien']} **Subastas VIP del Diván**

*[Con respeto genuino]*

Bienvenido a las subastas exclusivas. Aquí Diana ofrece... intimidades que no comparte con cualquiera.

**Tu nivel de acceso:** {self._get_vip_auction_level(narrative_state)}

*[Susurrando confidencialmente]*
Estos no son simples premios. Son... invitaciones a conocerla más profundamente.
            """.strip()

    # ===== MENSAJES DE ERROR Y SISTEMA =====

    def error_message(self, error_type: str, user: User) -> str:
        """Manejo elegante de errores con personalidad de Lucien"""

        error_responses = {
            "generic": f"""
{self.EMOJIS['lucien']} **Un Pequeño Inconveniente**

*[Suspirando con dramatismo elegante]*

Ah, la tecnología. Incluso en el mundo digital de Diana, ocasionalmente las cosas se complican de maneras inesperadas.

*[Ajustándose los guantes con aire profesional]*

Permíteme un momento para resolver esto con la gracia que la situación merece. Diana detesta los inconvenientes técnicos tanto como yo.

**¿Podrías intentar de nuevo, {user.first_name}?**
            """.strip(),
            "permission": f"""
{self.EMOJIS['lucien']} **Acceso Restringido**

*[Con aire de disculpa elegante]*

Me temo que esta función requiere un nivel de proximidad a Diana que aún no has alcanzado, {user.first_name}.

*[Con sonrisa comprensiva]*

Pero no te desanimes. Diana valora la paciencia y la dedicación por encima de la prisa.
            """.strip(),
            "rate_limit": f"""
{self.EMOJIS['lucien']} **Paciencia, {user.first_name}**

*[Con humor seco]*

La impaciencia raramente impresiona a Diana. Permíteme sugerir un momento de contemplación antes de continuar.

*[Consultando su reloj elegante]*

Los mejores placeres se saborean con... moderación.
            """.strip(),
        }

        return error_responses.get(error_type, error_responses["generic"])

    def maintenance_message(self) -> str:
        """Mensaje de mantenimiento con estilo"""

        return f"""
{self.EMOJIS['lucien']} **Mantenimiento del Santuario**

*[Con aire de disculpa elegante]*

Diana ha solicitado algunas... mejoras en nuestro espacio digital. Como buen mayordomo, debo asegurarme de que todo esté perfecto para su regreso.

{self.EMOJIS['elegant']} **Tiempo estimado:** 15-30 minutos

*[Con una reverencia]*

Agradezco tu paciencia mientras preparamos una experiencia aún más... extraordinaria.
        """.strip()

    # ===== MÉTODOS AUXILIARES PARA PERSONALIZACIÓN =====

    def _get_archetype_recognition(self, archetype: Optional[UserArchetype]) -> str:
        """Reconocimiento del arquetipo del usuario"""

        if not archetype:
            return "Diana aún está... estudiándote."

        archetype_comments = {
            UserArchetype.EXPLORER: "*[Con apreciación]*\nDiana ha notado tu atención al detalle. Encuentra esa curiosidad meticulosa... refrescante.",
            UserArchetype.DIRECT: "*[Con respeto]*\nTu honestidad directa ha capturado la atención de Diana. Aprecia a quienes no se pierden en rodeos innecesarios.",
            UserArchetype.ROMANTIC: "*[Con sonrisa conocedora]*\nDiana se siente intrigada por tu naturaleza romántica. Hay poesía en cómo te aproximas a ella.",
            UserArchetype.ANALYTICAL: "*[Con aprobación intelectual]*\nTu mente analítica fascina a Diana. Aprecia a quienes buscan comprensión profunda.",
            UserArchetype.PERSISTENT: "*[Con admiración]*\nTu persistencia ha impresionado a Diana. Pocos mantienen esa dedicación constante.",
            UserArchetype.PATIENT: "*[Con respeto profundo]*\nDiana valora enormemente tu paciencia. Comprende que las mejores cosas no deben apresurarse.",
        }

        return archetype_comments.get(
            archetype, "Diana te observa con creciente interés."
        )

    def _format_narrative_progress(self, narrative_state: UserNarrativeState) -> str:
        """Formatea el progreso narrativo del usuario"""

        level_descriptions = {
            NarrativeLevel.LEVEL_1_KINKY: "Explorando Los Kinkys",
            NarrativeLevel.LEVEL_2_KINKY_DEEP: "Profundizando en Los Kinkys",
            NarrativeLevel.LEVEL_3_KINKY_FINAL: "Culminación de Los Kinkys",
            NarrativeLevel.LEVEL_4_DIVAN_ENTRY: "Entrada al Diván",
            NarrativeLevel.LEVEL_5_DIVAN_DEEP: "Intimidad del Diván",
            NarrativeLevel.LEVEL_6_DIVAN_SUPREME: "Máxima Proximidad",
        }

        return level_descriptions.get(
            narrative_state.current_level, "Comenzando la aventura"
        )

    def _get_diana_mood(self, narrative_state: UserNarrativeState) -> str:
        """Estado de ánimo actual de Diana hacia el usuario"""

        trust_level = narrative_state.diana_trust_level

        if trust_level >= 90:
            return "en un estado de confianza excepcional"
        elif trust_level >= 70:
            return "intrigada y receptiva"
        elif trust_level >= 50:
            return "observando con interés creciente"
        elif trust_level >= 30:
            return "evaluando tu potencial"
        else:
            return "manteniendo su distancia habitual"

    def _get_diana_current_state(self, narrative_state: UserNarrativeState) -> str:
        """Estado actual de Diana para el menú principal"""

        states = [
            "contemplando sus próximos movimientos",
            "observando desde las sombras",
            "reflexionando sobre conexiones auténticas",
            "evaluando a quienes la buscan",
            "preparando nuevos misterios",
        ]

        # Seleccionar basado en el nivel de relación
        if narrative_state.diana_trust_level > 70:
            return "esperando con anticipación"
        else:
            return random.choice(states)

    def _get_personalized_menu_intro(self, narrative_state: UserNarrativeState) -> str:
        """Introducción personalizada del menú"""

        if narrative_state.primary_archetype == UserArchetype.EXPLORER:
            return "*[Con una sonrisa conocedora]*\nPuedo ver esa familiar hambre de descubrimiento en tus ojos..."
        elif narrative_state.primary_archetype == UserArchetype.ROMANTIC:
            return "*[Con elegancia poética]*\nDiana aprecia el romanticismo auténtico, algo cada vez más raro..."
        else:
            return "*[Con aire profesional]*\nPermíteme presentarte las opciones disponibles..."

    def _get_mission_encouragement_by_archetype(
        self, archetype: Optional[UserArchetype]
    ) -> str:
        """Aliento para misiones según arquetipo"""

        if archetype == UserArchetype.PERSISTENT:
            return "*[Con admiración]*\nTu persistencia no ha pasado desapercibida. Diana respeta esa cualidad."
        elif archetype == UserArchetype.PATIENT:
            return "*[Con aprobación]*\nTu paciencia es una virtud que Diana encuentra... magnética."
        else:
            return "*[Con aire alentador]*\nDiana valora el esfuerzo auténtico por encima de todo."

    def _get_mission_context_by_level(self, level: NarrativeLevel) -> str:
        """Contexto de misiones según nivel narrativo"""

        if level in [NarrativeLevel.LEVEL_1_KINKY, NarrativeLevel.LEVEL_2_KINKY_DEEP]:
            return "*[Con aire educativo]*\nEstas misiones son tu oportunidad de demostrar que mereces conocer más sobre Diana."
        elif level in [
            NarrativeLevel.LEVEL_4_DIVAN_ENTRY,
            NarrativeLevel.LEVEL_5_DIVAN_DEEP,
        ]:
            return "*[Con respeto creciente]*\nEn el Diván, las misiones se vuelven más... íntimas. Diana confía en ti."
        else:
            return "*[Con profesionalismo]*\nCada misión es una oportunidad de crecimiento."

    def _get_completion_style_comment(self, narrative_state: UserNarrativeState) -> str:
        """Comentario sobre el estilo de completar misiones"""

        if narrative_state.primary_archetype == UserArchetype.DIRECT:
            return "*[Con aprobación]*\nTu eficiencia directa impresiona a Diana. Sin rodeos innecesarios."
        elif narrative_state.primary_archetype == UserArchetype.EXPLORER:
            return "*[Con satisfacción]*\nTu atención meticulosa a cada detalle ha sido notada por Diana."
        else:
            return "*[Con elegancia]*\nCompletada con el estilo que Diana ha llegado a esperar de ti."

    def _get_diana_completion_whisper(self, narrative_state: UserNarrativeState) -> str:
        """Susurro especial de Diana para misiones completadas"""

        whispers = [
            "Cada misión completada me revela más sobre quién eres realmente...",
            "Tu dedicación no pasa desapercibida para mí...",
            "Hay algo hermoso en cómo te comprometes con cada tarea...",
            "Me gusta ver cómo creces con cada desafío que superas...",
        ]

        return random.choice(whispers)

    def _get_game_context_by_archetype(self, archetype: Optional[UserArchetype]) -> str:
        """Contexto de juegos según arquetipo"""

        if archetype == UserArchetype.ANALYTICAL:
            return "*[Con interés intelectual]*\nDiana está particularmente interesada en ver cómo tu mente analítica aborda estos desafíos."
        elif archetype == UserArchetype.EXPLORER:
            return "*[Con anticipación]*\nTu naturaleza exploradora hará estos juegos especialmente... reveladores para Diana."
        else:
            return "*[Con curiosidad]*\nDiana encuentra fascinante observar cómo diferentes personas enfrentan los mismos desafíos."

    def _get_performance_analysis(
        self, game_type: str, score: int, performance: str
    ) -> str:
        """Análisis del rendimiento en juegos"""

        if score >= 90:
            return "Rendimiento excepcional. Diana ha tomado nota especial de tu habilidad."
        elif score >= 70:
            return "Sólido desempeño. Diana aprecia la competencia cuando viene acompañada de elegancia."
        elif score >= 50:
            return "Desempeño respetable. Diana valora el esfuerzo auténtico por encima de la perfección."
        else:
            return "El valor está en el intento, no en la perfección. Diana comprende esto mejor que nadie."

    def _get_diana_observation_comment(
        self, score: int, narrative_state: UserNarrativeState
    ) -> str:
        """Comentario de observación de Diana sobre el juego"""

        if narrative_state.diana_trust_level > 70:
            return f"""
{self.EMOJIS['diana']} *Diana observa desde su espacio privado:*
"*Me gusta cómo no permites que el resultado defina tu valor...*"
            """.strip()
        else:
            return "*[Observando discretamente]*\nDiana toma nota mental de tu aproximación. Todo es información para ella."

    def _get_auction_eligibility_message(
        self, narrative_state: UserNarrativeState
    ) -> str:
        """Mensaje de elegibilidad para subastas"""

        if narrative_state.current_level == NarrativeLevel.NEWCOMER:
            return "*[Con aire restrictivo]*\nLas subastas más exclusivas requieren que Diana te conozca mejor primero."
        else:
            return "*[Con aprobación]*\nTu progreso te ha ganado acceso a subastas más... significativas."

    def _get_vip_auction_level(self, narrative_state: UserNarrativeState) -> str:
        """Nivel de acceso VIP a subastas"""

        trust = narrative_state.diana_trust_level

        if trust >= 90:
            return "Acceso total - Diana confía en ti completamente"
        elif trust >= 70:
            return "Acceso elevado - Diana te considera digno de confianza"
        elif trust >= 50:
            return "Acceso estándar - Diana está evaluando tu potencial"
        else:
            return "Acceso inicial - Diana te observa con interés"

    def _generic_welcome(self, user: User) -> str:
        """Mensaje de bienvenida genérico"""

        return f"""
{self.EMOJIS['lucien']} **Bienvenido de vuelta, {user.first_name}**

*[Con elegancia profesional]*

Siempre es un placer asistir a quienes comprenden el valor de la persistencia. Diana aprecia la constancia.

¿En qué puedo asistirte en tu búsqueda de proximidad a ella?
        """.strip()
   