from sqlalchemy import select

from database_init import get_session
from models.gamification import UserMission, Mission


class GamificationService:
    async def update_progress(self, user_mission_id: int, increment: int = 1) -> UserMission:
        async for session in get_session():
            stmt = select(UserMission).where(UserMission.id == user_mission_id)
            result = await session.execute(stmt)
            user_mission = result.scalar_one_or_none()
            if user_mission is None:
                return None
            user_mission.progress += increment
            if user_mission.progress >= 1:
                user_mission.completed = True
            await session.commit()
            await session.refresh(user_mission)
            return user_mission

    async def claim_reward(self, user_mission_id: int) -> Mission:
        async for session in get_session():
            stmt = select(UserMission).where(UserMission.id == user_mission_id)
            result = await session.execute(stmt)
            user_mission = result.scalar_one_or_none()
            if user_mission is None or not user_mission.completed or user_mission.claimed:
                return None
            user_mission.claimed = True
            await session.commit()
            mission_stmt = select(Mission).where(Mission.id == user_mission.mission_id)
            mission_res = await session.execute(mission_stmt)
            return mission_res.scalar_one_or_none()

    async def get_unclaimed_completed(self, user_id: int) -> list[UserMission]:
        async for session in get_session():
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.completed == True,
                UserMission.claimed == False,
            )
            result = await session.execute(stmt)
            return result.scalars().all()
