from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from datetime import datetime
from config.database import Base


class MenuConfig(Base):
    """Configuración dinámica de menús"""

    __tablename__ = "menu_configs"

    id = Column(Integer, primary_key=True)
    menu_key = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    buttons_config = Column(JSON)
    user_role = Column(String(20), nullable=False)
    min_level = Column(Integer, default=0)
    max_level = Column(Integer, default=999)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MenuButton(Base):
    """Botones de menú configurables"""

    __tablename__ = "menu_buttons"

    id = Column(Integer, primary_key=True)
    menu_config_id = Column(Integer, nullable=False)
    button_text = Column(String(100), nullable=False)
    callback_data = Column(String(100), nullable=False)
    position_row = Column(Integer, default=0)
    position_col = Column(Integer, default=0)
    required_role = Column(String(20), default="free")
    min_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
