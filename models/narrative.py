from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config.database import Base as DBBase

Base = declarative_base()
Base = DBBase


class LorePiece(Base):
    __tablename__ = "lore_pieces"

    id = Column(Integer, primary_key=True, index=True)


class UserLorePiece(Base):
    __tablename__ = "user_lore_pieces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"))

    user = relationship("User", back_populates="lore_pieces")
    lore_piece = relationship("LorePiece")


class NarrativeProgress(Base):
    __tablename__ = "narrative_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))


class LoreCombination(Base):
    __tablename__ = "lore_combinations"

    id = Column(Integer, primary_key=True, index=True)
    piece_a_id = Column(Integer, ForeignKey("lore_pieces.id"))
    piece_b_id = Column(Integer, ForeignKey("lore_pieces.id"))
    result_piece_id = Column(Integer, ForeignKey("lore_pieces.id"))
