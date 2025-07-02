from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database_init import Base

class LorePiece(Base):
    __tablename__ = 'lore_pieces'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    rarity = Column(String(50))
    combinable_with = Column(String(50))
    combination_result = Column(String(50))

class UserBackpack(Base):
    __tablename__ = 'user_backpack'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey('lore_pieces.id'), nullable=False)
    obtained_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')
    lore_piece = relationship('LorePiece')
