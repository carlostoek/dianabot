from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database_init import Base

class VIPAccess(Base):
    __tablename__ = 'vip_access'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    channel_id = Column(Integer, nullable=False)
    access_granted = Column(DateTime, default=datetime.utcnow)
    access_expires = Column(DateTime)
    is_active = Column(Boolean, default=True)

    user = relationship('User')

class VIPToken(Base):
    __tablename__ = 'vip_tokens'

    id = Column(Integer, primary_key=True)
    token = Column(String(50), unique=True, nullable=False)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
