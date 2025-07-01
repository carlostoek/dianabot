
    from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class GameType(enum.Enum):
    TRIVIA = "trivia"
    NUMBER_GUESS = "number_guess"
    WORD_GAME = "word_game"
    MEMORY = "memory"
    MATH = "math"


class DifficultyLevel(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TriviaQuestion(Base):
    __tablename__ = "trivia_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(String(200), nullable=False)
    wrong_answer_1 = Column(String(200), nullable=False)
    wrong_answer_2 = Column(String(200), nullable=False)
    wrong_answer_3 = Column(String(200), nullable=False)

    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    category = Column(String(100), default="General")
    reward_besitos = Column(Integer, default=10)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_admin = Column(Integer, nullable=True)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_type = Column(Enum(GameType))

    # Estado del juego
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=100)

    # Datos del juego (JSON string)
    game_data = Column(Text)  # Para guardar estado específico del juego

    # Recompensas
    besitos_earned = Column(Integer, default=0)
    lore_piece_earned = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relaciones
    user = relationship("User")


class TriviaAnswer(Base):
    __tablename__ = "trivia_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("trivia_questions.id"))

    selected_answer = Column(String(200))
    is_correct = Column(Boolean)
    time_taken = Column(Float)  # Segundos
    besitos_earned = Column(Integer, default=0)

    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    question = relationship("TriviaQuestion")
   