from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.admin import Admin, AdminLevel, AdminPermission, AdminAction
from models.user import User
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Optional, List, Dict, Any
from services.channel_service import ChannelService
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class AdminService:
    """Servicio completo para gestión de administradores"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()
        self.channel_service = ChannelService()

        # Permisos por nivel de admin
        self.LEVEL_PERMISSIONS = {
            AdminLevel.MODERATOR: [
                AdminPermission.MANAGE_CHANNELS,
                AdminPermission.ACCESS_ANALYTICS,
            ],
            AdminLevel.ADMIN: [
                AdminPermission.MANAGE_CHANNELS,
                AdminPermission.ACCESS_ANALYTICS,
                AdminPermission.GENERATE_VIP_TOKENS,
                AdminPermission.MANAGE_USERS,
            ],
            AdminLevel.SUPER_ADMIN: [
                AdminPermission.MANAGE_CHANNELS,
                AdminPermission.ACCESS_ANALYTICS,
                AdminPermission.GENERATE_VIP_TOKENS,
                AdminPermission.MANAGE_USERS,
                AdminPermission.MANAGE_ADMINS,
                AdminPermission.SYSTEM_SETTINGS,
            ],
        }

    # ===== VERIFICACIÓN DE PERMISOS =====

    def is_admin(self, telegram_id: int) -> bool:
        """Verifica si un usuario es administrador activo"""
        admin = self.db.query(Admin).filter(
            and_(
                Admin.telegram_id == telegram_id,
                Admin.is_active == True
            )
        ).first()
        return admin is not None

    def get_admin(self, telegram_id: int) -> Optional[Admin]:
        """Obtiene información completa del administrador"""
        return self.db.query(Admin).filter(
            and_(
                Admin.telegram_id == telegram_id,
                Admin.is_active == True
            )
        ).first()

    def get_admin_level(self, telegram_id: int) -> str:
        """Obtiene el nivel de administrador"""
        admin = self.get_admin(telegram_id)
        if not admin:
            return "user"
        return admin.admin_level.value

    def has_permission(self, telegram_id: int, permission: AdminPermission) -> bool:
        """Verifica si el admin tiene un permiso específico"""
        admin = self.get_admin(telegram_id)
        if not admin:
            return False

        # Verificar permisos por nivel
        level_permissions = self.LEVEL_PERMISSIONS.get(admin.admin_level, [])
        if permission in level_permissions:
            return True

        # Verificar permisos específicos
        permission_map = {
            AdminPermission.GENERATE_VIP_TOKENS: admin.can_generate_vip_tokens,
            AdminPermission.MANAGE_CHANNELS: admin.can_manage_channels,
            AdminPermission.MANAGE_USERS: admin.can_manage_users,
            AdminPermission.ACCESS_ANALYTICS: admin.can_access_analytics,
            AdminPermission.MANAGE_ADMINS: admin.can_manage_admins,
            AdminPermission.SYSTEM_SETTINGS: admin.can_modify_system,
        }

        return permission_map.get(permission, False)

    def can_perform_action(self, telegram_id: int, action_type: str, **kwargs) -> Dict[str, Any]:
        """Verifica si puede realizar una acción específica con límites"""
        admin = self.get_admin(telegram_id)
        if not admin:
            return {"allowed": False, "reason": "No es administrador"}

        # Verificar límites específicos
        if action_type == "generate_vip_token":
            if not self.has_permission(telegram_id, AdminPermission.GENERATE_VIP_TOKENS):
                return {"allowed": False, "reason": "Sin permisos para generar tokens VIP"}
            
            # Verificar límite diario
            today = datetime.utcnow().date()
            tokens_today = self.db.query(AdminAction).filter(
                and_(
                    AdminAction.admin_telegram_id == telegram_id,
                    AdminAction.action_type == "generate_vip_token",
                    func.date(AdminAction.created_at) == today,
                    AdminAction.success == True
                )
            ).count()

            if tokens_today >= admin.max_vip_tokens_per_day:
                return {
                    "allowed": False, 
                    "reason": f"Límite diario alcanzado ({admin.max_vip_tokens_per_day} tokens)"
                }

        return {"allowed": True}

    def generate_vip_token(self, admin_telegram_id: int, token_type: str) -> Dict[str, Any]:
        """Genera un token VIP para un usuario específico"""

        # Verificar si el admin tiene permiso
        if not self.has_permission(admin_telegram_id, AdminPermission.GENERATE_VIP_TOKENS):
            return {"error": "Sin permisos para generar tokens VIP"}

        # Verificar límites diarios de generación
        can_generate = self.can_perform_action(admin_telegram_id, "generate_vip_token")
        if not can_generate["allowed"]:
            return {"error": can_generate["reason"]}

        # Lógica para generar el token mediante ChannelService
        token_info = self.channel_service.create_vip_token(admin_telegram_id, token_type)

        # Registrar acción
        self.log_admin_action(
            admin_telegram_id=admin_telegram_id,
            action_type=f"generate_{token_type}_vip_token",
            action_description=f"Token VIP {token_type}",
            success=token_info.get("success", False),
            error_message=token_info.get("error", "")
        )

        if token_info.get("success"):
            return {
                "success": True,
                "token": token_info["token"],
                "expiry": token_info["expiry"],
                "message": "Token VIP generado exitosamente."
            }
        else:
            return {"error": token_info.get("error", "Error desconocido al generar el token")}

    # ===== GESTIÓN DE ADMINISTRADORES =====

    def create_admin(
        self,
        telegram_id: int,
        admin_level: AdminLevel,
        created_by_telegram_id: int,
        user_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Crea nuevo administrador"""

        # Verificar que quien crea tiene permisos
        if not self.has_permission(created_by_telegram_id, AdminPermission.MANAGE_ADMINS):
            return {"error": "Sin permisos para crear administradores"}

        # Verificar que no existe ya
        existing_admin = self.get_admin(telegram_id)
        if existing_admin:
            return {"error": "El usuario ya es administrador"}

        # Configurar permisos según nivel
        permissions = self._get_default_permissions_for_level(admin_level)

        admin = Admin(
            telegram_id=telegram_id,
            username=user_data.get("username") if user_data else None,
            first_name=user_data.get("first_name") if user_data else None,
            last_name=user_data.get("last_name") if user_data else None,
            admin_level=admin_level,
            created_by_admin_id=self.get_admin(created_by_telegram_id).id,
            **permissions
        )

        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)

        # Log de la acción
        self.log_admin_action(
            admin_telegram_id=created_by_telegram_id,
            action_type="create_admin",
            target_user_id=telegram_id,
            action_description=f"Creado admin nivel {admin_level.value}",
            action_data=json.dumps({"new_admin_id": admin.id, "level": admin_level.value})
        )

        return {
            "success": True,
            "admin": admin,
            "message": self._generate_admin_creation_message(admin)
        }

    def create_first_admin_direct(
        self,
        telegram_id: int,

        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea el primer super admin sin verificación de permisos"""

        try:
            # Verificar que NO existan administradores
            existing_admins = self.get_all_admins(include_inactive=True)
            if existing_admins:
                return {"error": "Ya existen administradores en el sistema"}

            # Verificar que no existe ya este usuario como admin
            existing_admin = self.get_admin(telegram_id)
            if existing_admin:
                return {"error": "El usuario ya es administrador"}

            # Configurar permisos de Super Admin
            permissions = self._get_default_permissions_for_level(AdminLevel.SUPER_ADMIN)

            admin = Admin(
                telegram_id=telegram_id,
                username=user_data.get("username") if user_data else None,
                first_name=user_data.get("first_name") if user_data else None,
                last_name=user_data.get("last_name") if user_data else None,
                admin_level=AdminLevel.SUPER_ADMIN,
                created_by_admin_id=None,  # Se crea a sí mismo
                notes="Primer Super Admin del sistema",
                **permissions
            )

            self.db.add(admin)
            self.db.commit()
            self.db.refresh(admin)

            # Log de la acción histórica
            self.log_admin_action(
                admin_telegram_id=telegram_id,
                action_type="first_admin_created",
                action_description="Primer Super Admin creado en el sistema",
                action_data=json.dumps({
                    "first_admin_id": admin.id,
                    "telegram_id": telegram_id,
                    "created_at": datetime.utcnow().isoformat(),
                }),
            )

            return {
                "success": True,
                "admin": admin,
                "message": self._generate_admin_creation_message(admin),
            }

        except Exception as e:
            logger.error(f"Error creando primer admin: {e}", exc_info=True)
            return {"error": f"Error interno: {str(e)}"}


    def update_admin_permissions(
        self, 
        target_telegram_id: int, 
        updated_by_telegram_id: int,
        new_permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualiza permisos de un administrador"""

        # Verificar permisos del que actualiza
        if not self.has_permission(updated_by_telegram_id, AdminPermission.MANAGE_ADMINS):
            return {"error": "Sin permisos para modificar administradores"}

        admin = self.get_admin(target_telegram_id)
        if not admin:
            return {"error": "Administrador no encontrado"}

        # Actualizar permisos
        updatable_fields = [
            "can_generate_vip_tokens", "can_manage_channels", "can_manage_users",
            "can_access_analytics", "can_manage_admins", "can_modify_system",
            "max_vip_tokens_per_day", "max_channels_manageable"
        ]

        old_permissions = {}
        for field in updatable_fields:
            if field in new_permissions:
                old_permissions[field] = getattr(admin, field)
                setattr(admin, field, new_permissions[field])

        admin.updated_at = datetime.utcnow()
        self.db.commit()

        # Log de la acción
        self.log_admin_action(
            admin_telegram_id=updated_by_telegram_id,
            action_type="update_admin_permissions",
            target_user_id=target_telegram_id,
            action_description="Permisos actualizados",
            action_data=json.dumps({
                "old_permissions": old_permissions,
                "new_permissions": new_permissions
            })
        )

        return {
            "success": True,
            "message": f"Permisos actualizados para {admin.first_name or admin.username}"
        }

    def deactivate_admin(
        self, 
        target_telegram_id: int, 
        deactivated_by_telegram_id: int,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Desactiva un administrador"""

        if not self.has_permission(deactivated_by_telegram_id, AdminPermission.MANAGE_ADMINS):
            return {"error": "Sin permisos para desactivar administradores"}

        admin = self.get_admin(target_telegram_id)
        if not admin:
            return {"error": "Administrador no encontrado"}

        admin.is_active = False
        admin.notes = f"Desactivado: {reason}" if reason else "Desactivado"
        admin.updated_at = datetime.utcnow()
        self.db.commit()

        # Log de la acción
        self.log_admin_action(
            admin_telegram_id=deactivated_by_telegram_id,
            action_type="deactivate_admin",
            target_user_id=target_telegram_id,
            action_description=f"Admin desactivado: {reason}",
            action_data=json.dumps({"reason": reason})
        )

        return {
            "success": True,
            "message": f"Administrador {admin.first_name or admin.username} desactivado"
        }

    # ===== LOGGING DE ACCIONES =====

    def log_admin_action(
        self,
        admin_telegram_id: int,
        action_type: str,
        target_user_id: int = None,
        target_channel_id: int = None,
        action_description: str = "",
        action_data: str = "",
        success: bool = True,
        error_message: str = ""
    ) -> AdminAction:
        """Registra acción de administrador"""

        action = AdminAction(
            admin_telegram_id=admin_telegram_id,
            action_type=action_type,
            target_user_id=target_user_id,
            target_channel_id=target_channel_id,
            action_description=action_description,
            action_data=action_data,
            success=success,
            error_message=error_message
        )

        self.db.add(action)

        # Actualizar estadísticas del admin
        admin = self.get_admin(admin_telegram_id)
        if admin:
            admin.total_commands_used += 1
            admin.last_command_used = action_type
            admin.last_activity = datetime.utcnow()

        self.db.commit()
        self.db.refresh(action)

        return action

    def update_admin_activity(self, telegram_id: int, command_used: str = None):
        """Actualiza actividad del administrador"""
        admin = self.get_admin(telegram_id)
        if admin:
            admin.last_activity = datetime.utcnow()
            if command_used:
                admin.last_command_used = command_used
                admin.total_commands_used += 1
            self.db.commit()

    # ===== CONSULTAS Y ESTADÍSTICAS =====

    def get_all_admins(self, include_inactive: bool = False) -> List[Admin]:
        """Obtiene lista de todos los administradores"""
        query = self.db.query(Admin)
        if not include_inactive:
            query = query.filter(Admin.is_active == True)
        return query.order_by(Admin.admin_level.desc(), Admin.created_at).all()

    def get_admin_statistics(self, telegram_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de un administrador"""
        admin = self.get_admin(telegram_id)
        if not admin:
            return {"error": "Administrador no encontrado"}

        # Acciones en los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_actions = self.db.query(AdminAction).filter(
            and_(
                AdminAction.admin_telegram_id == telegram_id,
                AdminAction.created_at >= thirty_days_ago
            )
        ).count()

        # Acciones por tipo
        action_types = self.db.query(
            AdminAction.action_type,
            func.count(AdminAction.id).label('count')
        ).filter(
            AdminAction.admin_telegram_id == telegram_id
        ).group_by(AdminAction.action_type).all()

        return {
            "admin_info": {
                "level": admin.admin_level.value,
                "active": admin.is_active,
                "created_at": admin.created_at.isoformat(),
                "last_activity": admin.last_activity.isoformat() if admin.last_activity else None,
            },
            "activity": {
                "total_commands": admin.total_commands_used,
                "last_command": admin.last_command_used,
                "recent_actions_30d": recent_actions,
            },
            "permissions": {
                "can_generate_vip_tokens": admin.can_generate_vip_tokens,
                "can_manage_channels": admin.can_manage_channels,
                "can_manage_users": admin.can_manage_users,
                "can_access_analytics": admin.can_access_analytics,
                "can_manage_admins": admin.can_manage_admins,
                "can_modify_system": admin.can_modify_system,
            },
            "limits": {
                "max_vip_tokens_per_day": admin.max_vip_tokens_per_day,
                "max_channels_manageable": admin.max_channels_manageable,
            },
            "action_breakdown": {action_type: count for action_type, count in action_types}
        }

    def get_admin_actions_log(
        self,
        telegram_id: int = None,
        action_type: str = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AdminAction]:
        """Obtiene log de acciones de administradores"""

        query = self.db.query(AdminAction)

        if telegram_id:
            query = query.filter(AdminAction.admin_telegram_id == telegram_id)

        if action_type:
            query = query.filter(AdminAction.action_type == action_type)

        if days:
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(AdminAction.created_at >= since_date)

        return query.order_by(desc(AdminAction.created_at)).limit(limit).all()

    # ===== MÉTODOS AUXILIARES =====

    def _get_default_permissions_for_level(self, admin_level: AdminLevel) -> Dict[str, Any]:
        """Obtiene permisos por defecto según el nivel de administrador"""
        
        if admin_level == AdminLevel.MODERATOR:
            return {
                "can_generate_vip_tokens": False,
                "can_manage_channels": True,
                "can_manage_users": False,
                "can_access_analytics": True,
                "can_manage_admins": False,
                "can_modify_system": False,
                "max_vip_tokens_per_day": 0,
                "max_channels_manageable": 3,
            }
        
        elif admin_level == AdminLevel.ADMIN:
            return {
                "can_generate_vip_tokens": True,
                "can_manage_channels": True,
                "can_manage_users": True,
                "can_access_analytics": True,
                "can_manage_admins": False,
                "can_modify_system": False,
                "max_vip_tokens_per_day": 10,
                "max_channels_manageable": 10,
            }
        
        elif admin_level == AdminLevel.SUPER_ADMIN:
            return {
                "can_generate_vip_tokens": True,
                "can_manage_channels": True,
                "can_manage_users": True,
                "can_access_analytics": True,
                "can_manage_admins": True,
                "can_modify_system": True,
                "max_vip_tokens_per_day": 999,  # Prácticamente ilimitado
                "max_channels_manageable": 999,
            }
        
        else:
            # Permisos mínimos por defecto
            return {
                "can_generate_vip_tokens": False,
                "can_manage_channels": False,
                "can_manage_users": False,
                "can_access_analytics": False,
                "can_manage_admins": False,
                "can_modify_system": False,
                "max_vip_tokens_per_day": 0,
                "max_channels_manageable": 0,
            }

    def _generate_admin_creation_message(self, admin: Admin) -> str:
        """Genera mensaje de confirmación de creación de admin"""
        
        level_messages = {
            AdminLevel.MODERATOR: "Un nuevo moderador se une al equipo",
            AdminLevel.ADMIN: "Un nuevo administrador ha sido designado",
            AdminLevel.SUPER_ADMIN: "Un nuevo Super Administrador ha ascendido"
        }
        
        level_msg = level_messages.get(admin.admin_level, "Nuevo administrador creado")
        
        return f"""
{self.lucien.EMOJIS['lucien']} *[Con aire ceremonioso]*

"*{level_msg}.*"

👑 **Administrador Creado Exitosamente**

**Información:**
• Nombre: {admin.first_name or 'N/A'}
• Username: @{admin.username or 'N/A'}
• Nivel: {admin.admin_level.value.title()}
• ID: {admin.id}

**Permisos otorgados:**
• Generar tokens VIP: {'✅' if admin.can_generate_vip_tokens else '❌'}
• Gestionar canales: {'✅' if admin.can_manage_channels else '❌'}
• Gestionar usuarios: {'✅' if admin.can_manage_users else '❌'}
• Ver analytics: {'✅' if admin.can_access_analytics else '❌'}
• Gestionar admins: {'✅' if admin.can_manage_admins else '❌'}

*[Con aire profesional]*

"*Diana ha sido informada del nombramiento.*"
        """.strip()

    async def get_pending_requests(self):
        """Obtiene solicitudes pendientes de administrador"""
        try:
            # Por ahora retorna lista vacía, implementar según tu lógica de BD
            return []
        except Exception as e:
            print(f"Error getting pending requests: {e}")
            return []
    
