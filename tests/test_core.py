from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
import pytest
from services.user_service import UserService
from services.mission_service import MissionService
from services.game_service import GameService


class TestCoreServices:
    """Tests críticos para servicios principales"""

    def setup_method(self):
        """Setup para cada test"""
        self.user_service = UserService()
        self.mission_service = MissionService()
        self.game_service = GameService()

        # Usuario de prueba
        self.test_user_data = {
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_user_creation(self):
        """Test creación de usuario"""
        user = self.user_service.get_or_create_user(self.test_user_data)

        assert user.first_name == "Test"
        assert user.telegram_id == 123456789
        assert user.besitos >= 0

    def test_narrative_progression(self):
        """Test progresión narrativa"""
        user = self.user_service.get_or_create_user(self.test_user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user.id)

        assert narrative_state.current_level is not None
        assert narrative_state.diana_trust_level >= 0

    def test_game_session(self):
        """Test sesión de juego"""
        user = self.user_service.get_or_create_user(self.test_user_data)

        from models.game import GameType

        session = self.game_service.start_game_session(
            user.id, GameType.RIDDLE
        )

        assert session["success"] == True
        assert "session_id" in session
        assert "game_data" in session


if __name__ == "__main__":
    pytest.main(["-v"])
   