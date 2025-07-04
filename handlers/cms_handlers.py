from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from cms.storyboard_manager import StoryboardManager
from cms.content_manager import ContentManager
from services.narrative_service import NarrativeService
from utils.keyboards import create_cms_keyboard
from utils.decorators import admin_required

class CMSHandlers:
    def __init__(self):
        self.router = Router()
        self.storyboard_manager = StoryboardManager()
        self.content_manager = ContentManager()
        self.narrative_service = NarrativeService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        
        self.router.callback_query.register(
            self.handle_cms_main,
            F.data == "admin_cms"
        )
        self.router.callback_query.register(
            self.handle_storyboard_editor,
            F.data == "cms_storyboard"
        )
        self.router.callback_query.register(
            self.handle_content_editor,
            F.data == "cms_content"
        )
        self.router.callback_query.register(
            self.handle_narrative_levels,
            F.data == "cms_narrative_levels"
        )
        self.router.callback_query.register(
            self.handle_edit_scene,
            F.data.startswith("edit_scene_")
        )

    @admin_required
    async def handle_cms_main(self, callback: CallbackQuery, user: dict, admin: dict):
        """Panel principal del CMS"""
        await callback.answer()
        
        cms_stats = await self.content_manager.get_cms_stats()
        
        cms_text = f"""📝 *Sistema de Gestión de Contenido*

🎭 **Estado del Contenido:**
• Escenas narrativas: {cms_stats.get('total_scenes', 0)}
• Niveles narrativos: {cms_stats.get('narrative_levels', 6)}
• Plantillas activas: {cms_stats.get('active_templates', 0)}
• Contenido personalizable: {cms_stats.get('customizable_content', 0)}

📚 **Distribución por Nivel:**
• Nivel 1 (Los Kinkys): {cms_stats.get('level_1_scenes', 0)} escenas
• Nivel 2 (Los Kinkys+): {cms_stats.get('level_2_scenes', 0)} escenas
• Nivel 3 (Los Kinkys++): {cms_stats.get('level_3_scenes', 0)} escenas
• Nivel 4 (El Diván): {cms_stats.get('level_4_scenes', 0)} escenas
• Nivel 5 (El Diván+): {cms_stats.get('level_5_scenes', 0)} escenas
• Nivel 6 (El Diván++): {cms_stats.get('level_6_scenes', 0)} escenas

🔧 **Herramientas de Edición:**
• Editor visual de storyboard
• Gestor de contenido dinámico
• Personalizador por arquetipo
• Previsualizador en tiempo real

⚡ **Últimas Modificaciones:**"""

        recent_changes = cms_stats.get('recent_changes', [])
        for change in recent_changes[:3]:
            cms_text += f"\n• {change.get('description', 'Cambio sin descripción')}"

        keyboard = create_cms_keyboard(admin)
        
        await callback.message.edit_text(
            cms_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_storyboard_editor(self, callback: CallbackQuery, user: dict, admin: dict):
        """Editor de storyboard"""
        await callback.answer()
        
        storyboard_stats = await self.storyboard_manager.get_storyboard_overview()
        
        storyboard_text = f"""🎬 *Editor de Storyboard*

📖 **Estructura Narrativa Actual:**

🔹 **Nivel 1 - Los Kinkys (Canal Free):**
  └── Escena 1: Bienvenida de Diana
  └── Escena 2: Lucien y el Primer Desafío
  └── Escena 3: Respuesta Personalizada (2 variantes)
  └── Escena 4: La Primera Pista

🔹 **Nivel 2 - Los Kinkys (Profundización):**
  └── Escena 1: El Regreso Observado
  └── Escena 2: Desafío de Observación
  └── Escena 3: Reconocimiento Profundo

🔹 **Nivel 4 - El Diván (Canal VIP):**
  └── Escena 1: Bienvenida Íntima
  └── Escena 2: Desafío Profundo
  └── Escena 3: Evaluación de Comprensión

📊 **Métricas de Flujo:**
• Usuarios que completan Nivel 1: {storyboard_stats.get('level_1_completion', 0)}%
• Conversión Free → VIP: {storyboard_stats.get('free_to_vip_conversion', 0)}%
• Retención en Nivel 4: {storyboard_stats.get('level_4_retention', 0)}%

🎯 **Puntos de Decisión Críticos:**
• Reacción al primer mensaje (Nivel 1)
• Evaluación de comprensión (Nivel 4)
• Síntesis narrativa completa (Nivel 6)

✏️ **Herramientas de Edición:**
• Agregar nuevas escenas
• Modificar triggers de progresión
• Personalizar por arquetipo de usuario
• Configurar recompensas"""

        keyboard = create_cms_keyboard(admin, section="storyboard")
        
        await callback.message.edit_text(
            storyboard_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_content_editor(self, callback: CallbackQuery, user: dict, admin: dict):
        """Editor de contenido dinámico"""
        await callback.answer()
        
        content_stats = await self.content_manager.get_content_stats()
        
        content_text = f"""📝 *Editor de Contenido Dinámico*

🎭 **Contenido Personalizable:**

**Variables Disponibles:**
• {{user_name}} - Nombre del usuario
• {{user_level}} - Nivel actual
• {{user_besitos}} - Besitos actuales
• {{user_archetype}} - Arquetipo detectado
• {{narrative_level}} - Progreso narrativo

**Arquetipos Activos:**
• Explorador: {content_stats.get('explorer_users', 0)} usuarios
• Directo: {content_stats.get('direct_users', 0)} usuarios
• Romántico: {content_stats.get('romantic_users', 0)} usuarios
• Analítico: {content_stats.get('analytical_users', 0)} usuarios

📚 **Plantillas de Mensajes:**

**1. Diana - Personalizada por Arquetipo:**
      
