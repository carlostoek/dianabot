from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from services.mission_service import MissionService
from services.gamification_service import GamificationService
from keyboards.inline import mission_accept_kb, minigame_kb
from states.user_states import Gamification
from utils.decorators import onboarding_required

router = Router()
mission_service = MissionService()
gamification_service = GamificationService()


@router.message(commands=["misiones", "mision"])
@onboarding_required
async def show_daily_mission(message: types.Message, state: FSMContext, user):
    user_mission = await mission_service.assign_daily_mission(user.id)
    if user_mission is None:
        await message.answer("No hay misiones disponibles por ahora.")
        return
    mission = await mission_service.get_mission_details(user_mission.mission_id)
    await message.answer(
        f"🎯 {mission.title}\n{mission.description}",
        reply_markup=mission_accept_kb(user_mission.id).as_markup(),
    )
    await state.update_data(mission_id=user_mission.id)
    await state.set_state(Gamification.selecting_mission)


@router.callback_query(Gamification.selecting_mission, F.data.startswith("accept_mission:"))
async def accept_mission(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Has aceptado la misión. Prepárate para perder el tiempo.",
        reply_markup=minigame_kb().as_markup(),
    )
    await state.set_state(Gamification.playing_minigame)


@router.callback_query(Gamification.playing_minigame, F.data == "play_minigame")
async def play_minigame(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mission_id = data.get("mission_id")
    if mission_id:
        await gamification_service.update_progress(mission_id)
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Minijuego completado. Usa /reclamar para tu magnífica recompensa."
    )


@router.message(commands=["reclamar"])
@onboarding_required
async def claim_reward(message: types.Message, user):
    missions = await gamification_service.get_unclaimed_completed(user.id)
    if not missions:
        await message.answer("Nada que reclamar. Sigue intentándolo.")
        return
    mission = missions[0]
    details = await gamification_service.claim_reward(mission.id)
    if details:
        await message.answer(
            f"🎁 Recompensa obtenida: {details.reward_besitos} 💎 Besitos"
        )
    else:
        await message.answer("Algo salió mal al reclamar tu recompensa.")

