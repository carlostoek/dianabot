from datetime import datetime
from random import choice
from sqlalchemy import select, insert

from database_init import get_session
from models.gamification import Mission, UserMission


class MissionService:
    async def assign_daily_mission(self, user_id: int) -> UserMission:
        async for session in get_session():
            stmt = select(UserMission).join(Mission).where(
                UserMission.user_id == user_id,
                Mission.mission_type == "daily",
                UserMission.completed == False,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            mission_stmt = select(Mission).where(Mission.mission_type == "daily")
            missions = (await session.execute(mission_stmt)).scalars().all()
            if not missions:
                return None
            mission = choice(missions)
            user_mission = UserMission(user_id=user_id, mission_id=mission.id)
            session.add(user_mission)
            await session.commit()
            await session.refresh(user_mission)
            return user_mission

    async def get_mission_details(self, mission_id: int) -> Mission:
        async for session in get_session():
            stmt = select(Mission).where(Mission.id == mission_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
