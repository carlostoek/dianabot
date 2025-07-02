from sqlalchemy import Column, Integer, String, ForeignKey
from config.database import Base


class LorePiece(Base):
    __tablename__ = 'lore_pieces'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))


class UserLorePiece(Base):
    __tablename__ = 'user_lore_pieces'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    lore_piece_id = Column(Integer, ForeignKey('lore_pieces.id'), primary_key=True)
