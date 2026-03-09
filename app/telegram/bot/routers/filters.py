from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.application.services.user_service import UserService
from app.domain.user.value_objects import FilterMode
from app.infrastructure.db import UserUnitOfWork, async_session_factory
from app.telegram.bot.keyboards import (
    CANCEL_BUTTON_TEXT,
    EXPERIENCE_FROM_1_TEXT,
    EXPERIENCE_FROM_3_TEXT,
    EXPERIENCE_FROM_5_TEXT,
    EXPERIENCE_IGNORE_TEXT,
    FORMAT_ANY_TEXT,
    FORMAT_HYBRID_TEXT,
    FORMAT_ONSITE_TEXT,
    FORMAT_REMOTE_TEXT,
    FORMAT_SOFT_TEXT,
    FORMAT_STRICT_TEXT,
    SALARY_SOFT_TEXT,
    SALARY_STRICT_TEXT,
    TRACKING_BUTTON_TEXT,
    get_filter_experience_kb,
    get_filter_format_kb,
    get_filter_salary_kb,
    get_main_menu_kb,
    get_start_kb,
)
from app.telegram.bot.states import BotStates
from app.telegram.bot.views.tracking_settings import (
    EXPERIENCE_STEP,
    FORMAT_STEP,
    SALARY_STEP,
    build_tracking_intro_and_available_steps,
)

router = Router()

EXP_MIN_MONTHS_KEY = "exp_min_months"
SALARY_MODE_KEY = "salary_mode"
FORMAT_MODE_KEY = "format_mode"
AVAILABLE_STEPS_KEY = "available_steps"
STEP_INDEX_KEY = "step_index"

EXPERIENCE_TEXT_TO_MIN_MONTHS: dict[str, int | None] = {
    EXPERIENCE_IGNORE_TEXT: None,
    EXPERIENCE_FROM_1_TEXT: 12,
    EXPERIENCE_FROM_3_TEXT: 36,
    EXPERIENCE_FROM_5_TEXT: 60,
}


def _experience_min_months_from_text(text: str) -> int | None:
    return EXPERIENCE_TEXT_TO_MIN_MONTHS.get(text)


async def _ask_current_step(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    steps = data.get(AVAILABLE_STEPS_KEY, [])
    step_index = int(data.get(STEP_INDEX_KEY, 0))
    if not isinstance(steps, list) or step_index >= len(steps):
        return False

    step = steps[step_index]
    if step == EXPERIENCE_STEP:
        await state.set_state(BotStates.filter_experience)
        await message.answer(
            "Как учитывать опыт?",
            reply_markup=get_filter_experience_kb(),
        )
        return True

    if step == SALARY_STEP:
        await state.set_state(BotStates.filter_salary)
        await message.answer(
            "Как учитывать зарплату?",
            reply_markup=get_filter_salary_kb(),
        )
        return True

    if step == FORMAT_STEP:
        await state.set_state(BotStates.filter_format)
        await message.answer(
            "Как учитывать формат работы из резюме?",
            reply_markup=get_filter_format_kb(),
        )
        return True

    return False


async def _finalize_filters(message: Message, state: FSMContext, service: UserService) -> None:
    if message.from_user is None:
        await state.clear()
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    data = await state.get_data()
    exp_min_months = data.get(EXP_MIN_MONTHS_KEY)
    salary_mode = FilterMode(data.get(SALARY_MODE_KEY, FilterMode.SOFT.value))
    format_mode = FilterMode(data.get(FORMAT_MODE_KEY, FilterMode.SOFT.value))

    user = await service.get_user_by_tg_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    updated = await service.update_filters(
        tg_id=message.from_user.id,
        experience_min_months=(exp_min_months if isinstance(exp_min_months, int) else None),
        salary_mode=salary_mode,
        work_format=user.cv_work_format,
        work_format_mode=format_mode,
    )
    if not updated:
        await state.clear()
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    await state.clear()
    await state.set_state(BotStates.main_menu)
    await message.answer(
        "Фильтры обновлены.",
        reply_markup=get_main_menu_kb(),
    )


async def _advance_or_finalize(message: Message, state: FSMContext, service: UserService) -> None:
    data = await state.get_data()
    step_index = int(data.get(STEP_INDEX_KEY, 0)) + 1
    await state.update_data({STEP_INDEX_KEY: step_index})
    has_next = await _ask_current_step(message, state)
    if has_next:
        return
    await _finalize_filters(message, state, service)


@router.message(
    StateFilter(BotStates.main_menu, BotStates.processing_resume, None),
    F.text == TRACKING_BUTTON_TEXT,
)
async def start_filter_wizard(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await state.clear()
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    service = UserService(UserUnitOfWork(async_session_factory))
    user = await service.get_user_by_tg_id(message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer(
            "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
            reply_markup=get_start_kb(),
        )
        return

    intro_text, available_steps = build_tracking_intro_and_available_steps(user)
    await message.answer(intro_text)

    await state.clear()
    if not available_steps:
        updated = await service.update_filters(
            tg_id=message.from_user.id,
            experience_min_months=None,
            salary_mode=FilterMode.SOFT,
            work_format=user.cv_work_format,
            work_format_mode=FilterMode.SOFT,
        )
        if not updated:
            await message.answer(
                "Нажмите «Начать пользоваться ботом», чтобы продолжить.",
                reply_markup=get_start_kb(),
            )
            return

        await state.set_state(BotStates.main_menu)
        await message.answer(
            "🚀 Загрузите более полное резюме, чтобы включить дополнительные фильтры и "
            "получать меньше шума.",
            reply_markup=get_main_menu_kb(),
        )
        return

    await state.update_data(
        {
            AVAILABLE_STEPS_KEY: available_steps,
            STEP_INDEX_KEY: 0,
            EXP_MIN_MONTHS_KEY: None,
            SALARY_MODE_KEY: FilterMode.SOFT.value,
            FORMAT_MODE_KEY: FilterMode.SOFT.value,
        }
    )
    await _ask_current_step(message, state)


@router.message(
    StateFilter(BotStates.filter_experience),
    F.text.in_(
        {
            EXPERIENCE_IGNORE_TEXT,
            EXPERIENCE_FROM_1_TEXT,
            EXPERIENCE_FROM_3_TEXT,
            EXPERIENCE_FROM_5_TEXT,
        }
    ),
)
async def filter_experience_step(message: Message, state: FSMContext) -> None:
    experience_min_months = _experience_min_months_from_text(message.text)
    await state.update_data({EXP_MIN_MONTHS_KEY: experience_min_months})
    service = UserService(UserUnitOfWork(async_session_factory))
    await _advance_or_finalize(message, state, service)


@router.message(
    StateFilter(BotStates.filter_salary),
    F.text.in_({SALARY_STRICT_TEXT, SALARY_SOFT_TEXT}),
)
async def filter_salary_step(message: Message, state: FSMContext) -> None:
    mode = FilterMode.STRICT if message.text == SALARY_STRICT_TEXT else FilterMode.SOFT
    await state.update_data({SALARY_MODE_KEY: mode.value})
    service = UserService(UserUnitOfWork(async_session_factory))
    await _advance_or_finalize(message, state, service)


@router.message(
    StateFilter(BotStates.filter_format),
    F.text.in_(
        {
            FORMAT_STRICT_TEXT,
            FORMAT_SOFT_TEXT,
            FORMAT_REMOTE_TEXT,
            FORMAT_HYBRID_TEXT,
            FORMAT_ONSITE_TEXT,
            FORMAT_ANY_TEXT,
        }
    ),
)
async def filter_format_step(message: Message, state: FSMContext) -> None:
    strict_values = {
        FORMAT_STRICT_TEXT,
        FORMAT_REMOTE_TEXT,
        FORMAT_HYBRID_TEXT,
        FORMAT_ONSITE_TEXT,
    }
    mode = FilterMode.STRICT if message.text in strict_values else FilterMode.SOFT
    await state.update_data({FORMAT_MODE_KEY: mode.value})
    service = UserService(UserUnitOfWork(async_session_factory))
    await _advance_or_finalize(message, state, service)


@router.message(
    StateFilter(
        BotStates.filter_experience,
        BotStates.filter_salary,
        BotStates.filter_format,
    ),
    F.text == CANCEL_BUTTON_TEXT,
)
async def cancel_filter_wizard(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BotStates.main_menu)
    await message.answer(
        "Настройка отменена.",
        reply_markup=get_main_menu_kb(),
    )
