from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from models.narrative_triggers import (
    NarrativeTrigger,
    TriggerTemplate,
    UserTriggerExecution,
)
from models.narrative_state import NarrativeScene, UserNarrativeState
from models.user import User
from config.database import get_db
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re


class NarrativeAdminService:
    """Servicio para administrar narrativa, escenas y triggers"""

    def __init__(self):
        self.db = next(get_db())

    # ===== GESTIÓN DE ESCENAS =====

    def create_scene(self, scene_data: Dict[str, Any]) -> NarrativeScene:
        """Crea una nueva escena narrativa"""

        scene = NarrativeScene(
            level=scene_data["level"],
            scene_key=scene_data["scene_key"],
            scene_order=scene_data.get("scene_order", 1),
            title=scene_data["title"],
            lucien_dialogue=scene_data.get("lucien_dialogue"),
            diana_dialogue=scene_data.get("diana_dialogue"),
            system_message=scene_data.get("system_message"),
            archetype_variations=scene_data.get("archetype_variations", {}),
            emotional_variations=scene_data.get("emotional_variations", {}),
            triggers=scene_data.get("triggers", {}),
            requirements=scene_data.get("requirements", {}),
            outcomes=scene_data.get("outcomes", {}),
            min_time_since_last=scene_data.get("min_time_since_last", 0),
            max_time_since_last=scene_data.get("max_time_since_last"),
            created_by=scene_data.get("created_by", "admin"),
        )

        self.db.add(scene)
        self.db.commit()
        self.db.refresh(scene)

        return scene

    def update_scene(
        self, scene_id: int, scene_data: Dict[str, Any]
    ) -> Optional[NarrativeScene]:
        """Actualiza una escena existente"""

        scene = (
            self.db.query(NarrativeScene).filter(NarrativeScene.id == scene_id).first()
        )
        if not scene:
            return None

        # Actualizar campos permitidos
        updatable_fields = [
            "title",
            "lucien_dialogue",
            "diana_dialogue",
            "system_message",
            "archetype_variations",
            "emotional_variations",
            "triggers",
            "requirements",
            "outcomes",
            "is_active",
        ]

        for field in updatable_fields:
            if field in scene_data:
                setattr(scene, field, scene_data[field])

        self.db.commit()
        return scene

    def get_scenes_by_level(self, level: str) -> List[NarrativeScene]:
        """Obtiene todas las escenas de un nivel"""

        return (
            self.db.query(NarrativeScene)
            .filter(
                and_(NarrativeScene.level == level, NarrativeScene.is_active == True)
            )
            .order_by(NarrativeScene.scene_order)
            .all()
        )

    def duplicate_scene(
        self, scene_id: int, new_scene_key: str
    ) -> Optional[NarrativeScene]:
        """Duplica una escena existente con nueva clave"""

        original = (
            self.db.query(NarrativeScene).filter(NarrativeScene.id == scene_id).first()
        )
        if not original:
            return None

        new_scene = NarrativeScene(
            level=original.level,
            scene_key=new_scene_key,
            scene_order=original.scene_order + 1,
            title=f"{original.title} (Copia)",
            lucien_dialogue=original.lucien_dialogue,
            diana_dialogue=original.diana_dialogue,
            system_message=original.system_message,
            archetype_variations=original.archetype_variations,
            emotional_variations=original.emotional_variations,
            triggers=original.triggers,
            requirements=original.requirements,
            outcomes=original.outcomes,
            min_time_since_last=original.min_time_since_last,
            max_time_since_last=original.max_time_since_last,
            created_by="admin_copy",
        )

        self.db.add(new_scene)
        self.db.commit()
        self.db.refresh(new_scene)

        return new_scene

    # ===== GESTIÓN DE TRIGGERS =====

    def create_trigger(self, trigger_data: Dict[str, Any]) -> NarrativeTrigger:
        """Crea un nuevo trigger narrativo"""

        trigger = NarrativeTrigger(
            name=trigger_data["name"],
            description=trigger_data.get("description"),
            trigger_key=trigger_data["trigger_key"],
            trigger_type=trigger_data["trigger_type"],
            frequency=trigger_data.get("frequency", "once"),
            priority=trigger_data.get("priority", 100),
            conditions=trigger_data["conditions"],
            user_filters=trigger_data.get("user_filters", {}),
            action_type=trigger_data["action_type"],
            action_config=trigger_data["action_config"],
            delay_seconds=trigger_data.get("delay_seconds", 0),
            cooldown_seconds=trigger_data.get("cooldown_seconds", 0),
            valid_from=trigger_data.get("valid_from"),
            valid_until=trigger_data.get("valid_until"),
            is_test_mode=trigger_data.get("is_test_mode", False),
            created_by=trigger_data.get("created_by", "admin"),
        )

        self.db.add(trigger)
        self.db.commit()
        self.db.refresh(trigger)

        return trigger

    def create_trigger_from_template(
        self, template_id: int, variables: Dict[str, Any]
    ) -> Optional[NarrativeTrigger]:
        """Crea trigger desde template con variables personalizadas"""

        template = (
            self.db.query(TriggerTemplate)
            .filter(TriggerTemplate.id == template_id)
            .first()
        )
        if not template:
            return None

        # Procesar template con variables
        processed_config = self._process_template_variables(
            template.template_config, variables
        )

        trigger_data = {
            "name": processed_config["name"],
            "description": processed_config["description"],
            "trigger_key": f"from_template_{template.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "trigger_type": processed_config["trigger_type"],
            "conditions": processed_config["conditions"],
            "action_type": processed_config["action_type"],
            "action_config": processed_config["action_config"],
            "created_by": f"template_{template.id}",
        }

        return self.create_trigger(trigger_data)

    def update_trigger(
        self, trigger_id: int, trigger_data: Dict[str, Any]
    ) -> Optional[NarrativeTrigger]:
        """Actualiza un trigger existente"""

        trigger = (
            self.db.query(NarrativeTrigger)
            .filter(NarrativeTrigger.id == trigger_id)
            .first()
        )
        if not trigger:
            return None

        updatable_fields = [
            "name",
            "description",
            "conditions",
            "user_filters",
            "action_config",
            "delay_seconds",
            "cooldown_seconds",
            "valid_from",
            "valid_until",
            "is_active",
            "is_test_mode",
            "priority",
        ]

        for field in updatable_fields:
            if field in trigger_data:
                setattr(trigger, field, trigger_data[field])

        trigger.updated_at = datetime.utcnow()
        self.db.commit()

        return trigger

    def get_active_triggers(
        self, trigger_type: Optional[str] = None
    ) -> List[NarrativeTrigger]:
        """Obtiene triggers activos, opcionalmente filtrados por tipo"""

        query = self.db.query(NarrativeTrigger).filter(
            and_(
                NarrativeTrigger.is_active == True,
                or_(
                    NarrativeTrigger.valid_from.is_(None),
                    NarrativeTrigger.valid_from <= datetime.utcnow(),
                ),
                or_(
                    NarrativeTrigger.valid_until.is_(None),
                    NarrativeTrigger.valid_until >= datetime.utcnow(),
                ),
            )
        )

        if trigger_type:
            query = query.filter(NarrativeTrigger.trigger_type == trigger_type)

        return query.order_by(desc(NarrativeTrigger.priority)).all()

    def test_trigger_conditions(self, trigger_id: int, user_id: int) -> Dict[str, Any]:
        """Prueba si un trigger se activaría para un usuario específico"""

        trigger = (
            self.db.query(NarrativeTrigger)
            .filter(NarrativeTrigger.id == trigger_id)
            .first()
        )
        if not trigger:
            return {"error": "Trigger no encontrado"}

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        # Evaluar condiciones
        from services.narrative_trigger_service import NarrativeTriggerService

        trigger_service = NarrativeTriggerService()

        result = trigger_service.evaluate_trigger_for_user(trigger, user)

        return {
            "trigger_name": trigger.name,
            "user_name": user.first_name,
            "would_trigger": result["matches"],
            "evaluation_details": result.get("details", {}),
            "missing_conditions": result.get("missing_conditions", []),
        }

    # ===== GESTIÓN DE TEMPLATES =====

    def create_trigger_template(self, template_data: Dict[str, Any]) -> TriggerTemplate:
        """Crea un template de trigger reutilizable"""

        template = TriggerTemplate(
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            template_config=template_data["template_config"],
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    def get_trigger_templates(
        self, category: Optional[str] = None
    ) -> List[TriggerTemplate]:
        """Obtiene templates de triggers"""

        query = self.db.query(TriggerTemplate).filter(TriggerTemplate.is_active == True)

        if category:
            query = query.filter(TriggerTemplate.category == category)

        return query.all()

    # ===== ANÁLISIS Y ESTADÍSTICAS =====

    def get_trigger_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene estadísticas de triggers"""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Triggers más utilizados
        trigger_usage = (
            self.db.query(NarrativeTrigger.name, NarrativeTrigger.times_triggered)
            .filter(NarrativeTrigger.last_triggered >= since_date)
            .order_by(desc(NarrativeTrigger.times_triggered))
            .limit(10)
            .all()
        )

        # Ejecuciones recientes
        recent_executions = (
            self.db.query(UserTriggerExecution)
            .filter(UserTriggerExecution.executed_at >= since_date)
            .count()
        )

        # Triggers activos
        active_triggers = (
            self.db.query(NarrativeTrigger)
            .filter(NarrativeTrigger.is_active == True)
            .count()
        )

        return {
            "period_days": days,
            "active_triggers": active_triggers,
            "recent_executions": recent_executions,
            "top_triggers": [
                {"name": name, "times_triggered": count}
                for name, count in trigger_usage
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_user_trigger_history(
        self, user_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de triggers para un usuario"""

        executions = (
            self.db.query(
                UserTriggerExecution,
                NarrativeTrigger.name,
                NarrativeTrigger.description,
            )
            .join(
                NarrativeTrigger, UserTriggerExecution.trigger_id == NarrativeTrigger.id
            )
            .filter(UserTriggerExecution.user_id == user_id)
            .order_by(desc(UserTriggerExecution.executed_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "trigger_name": name,
                "description": description,
                "executed_at": execution.executed_at.isoformat(),
                "success": execution.success,
                "context": execution.execution_context,
                "user_response": execution.user_response,
            }
            for execution, name, description in executions
        ]

    # ===== MÉTODOS AUXILIARES =====

    def _process_template_variables(
        self, template_config: Dict, variables: Dict[str, Any]
    ) -> Dict:
        """Procesa variables en template configuration"""

        # Convertir a string para hacer replacements
        config_str = json.dumps(template_config)

        # Reemplazar variables en formato {VARIABLE}
        for var_name, var_value in variables.items():
            pattern = f"{{{var_name}}}"
            config_str = config_str.replace(pattern, str(var_value))

            # También soportar expresiones simples como {X*10}
            pattern_expr = f"{{{var_name}\\*([0-9]+)}}"
            matches = re.findall(pattern_expr, config_str)
            for match in matches:
                multiplier = int(match)
                result = var_value * multiplier
                config_str = re.sub(
                    f"{{{var_name}\\*{multiplier}}}", str(result), config_str
                )

        # Convertir de vuelta a dict
        return json.loads(config_str)

    def export_narrative_config(self) -> Dict[str, Any]:
        """Exporta toda la configuración narrativa"""

        scenes = (
            self.db.query(NarrativeScene).filter(NarrativeScene.is_active == True).all()
        )
        triggers = (
            self.db.query(NarrativeTrigger)
            .filter(NarrativeTrigger.is_active == True)
            .all()
        )
        templates = (
            self.db.query(TriggerTemplate)
            .filter(TriggerTemplate.is_active == True)
            .all()
        )

        return {
            "export_date": datetime.utcnow().isoformat(),
            "scenes": [
                {
                    "level": scene.level.value,
                    "scene_key": scene.scene_key,
                    "title": scene.title,
                    "lucien_dialogue": scene.lucien_dialogue,
                    "diana_dialogue": scene.diana_dialogue,
                    "archetype_variations": scene.archetype_variations,
                    "emotional_variations": scene.emotional_variations,
                    "triggers": scene.triggers,
                    "requirements": scene.requirements,
                    "outcomes": scene.outcomes,
                }
                for scene in scenes
            ],
            "triggers": [
                {
                    "name": trigger.name,
                    "trigger_key": trigger.trigger_key,
                    "trigger_type": trigger.trigger_type.value,
                    "conditions": trigger.conditions,
                    "action_type": trigger.action_type,
                    "action_config": trigger.action_config,
                    "user_filters": trigger.user_filters,
                }
                for trigger in triggers
            ],
            "templates": [
                {
                    "name": template.name,
                    "category": template.category,
                    "template_config": template.template_config,
                }
                for template in templates
            ],
        }

    def import_narrative_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Importa configuración narrativa"""

        results = {
            "scenes_imported": 0,
            "triggers_imported": 0,
            "templates_imported": 0,
            "errors": [],
        }

        try:
            # Importar escenas
            for scene_data in config_data.get("scenes", []):
                try:
                    self.create_scene(scene_data)
                    results["scenes_imported"] += 1
                except Exception as e:
                    results["errors"].append(
                        f"Error importando escena {scene_data.get('scene_key')}: {str(e)}"
                    )

            # Importar triggers
            for trigger_data in config_data.get("triggers", []):
                try:
                    self.create_trigger(trigger_data)
                    results["triggers_imported"] += 1
                except Exception as e:
                    results["errors"].append(
                        f"Error importando trigger {trigger_data.get('name')}: {str(e)}"
                    )

            # Importar templates
            for template_data in config_data.get("templates", []):
                try:
                    self.create_trigger_template(template_data)
                    results["templates_imported"] += 1
                except Exception as e:
                    results["errors"].append(
                        f"Error importando template {template_data.get('name')}: {str(e)}"
                    )

        except Exception as e:
            results["errors"].append(f"Error general en importación: {str(e)}")

        return results
   