from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime
from enum import Enum

class AdminLevel(Enum):
    MODERATOR = "moderator"      # Puede moderar canales
    ADMIN = "admin"              # Puede generar tokens VIP
    SUPER_ADMIN = "super_admin"  # Acceso total

class AdminPermission(Enum):
    GENERATE_VIP_TOKENS = "generate_vip_tokens"
    MANAGE_CHANNELS = "manage_channels"
    MANAGE_USERS = "manage_users"
    ACCESS_ANALYTICS = "access_analytics"
    MANAGE_ADMINS = "manage_admins"
    SYSTEM_SETTINGS = "system_settings"

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Permisos
    admin_level = Column(SQLEnum(AdminLevel), default=AdminLevel.MODERATOR)
    is_active = Column(Boolean, default=True)
    
    # Permisos específicos
    can_generate_vip_tokens = Column(Boolean, default=False)
    can_manage_channels = Column(Boolean, default=True)
    can_manage_users = Column(Boolean, default=False)
    can_access_analytics = Column(Boolean, default=True)
    can_manage_admins = Column(Boolean, default=False)
    can_modify_system = Column(Boolean, default=False)
    
    # Restricciones
    max_vip_tokens_per_day = Column(Integer, default=10)
    max_channels_manageable = Column(Integer, default=5)
    
    # Metadata
    created_by_admin_id = Column(Integer, nullable=True)
    notes = Column(String(500))
    
    # Estadísticas de uso
    total_commands_used = Column(Integer, default=0)
    last_command_used = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Admin(telegram_id={self.telegram_id}, level={self.admin_level.value}, active={self.is_active})>"

class AdminAction(Base):
    """Log de acciones realizadas por administradores"""
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    admin_telegram_id = Column(BigInteger, nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    target_user_id = Column(BigInteger, nullable=True)
    target_channel_id = Column(BigInteger, nullable=True)
    
    # Detalles de la acción
    action_description = Column(String(500))
    action_data = Column(String(1000))  # JSON como string para datos específicos
    
    # Resultado
    success = Column(Boolean, default=True)
    error_message = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AdminAction(admin={self.admin_telegram_id}, action={self.action_type}, success={self.success})>"
      
