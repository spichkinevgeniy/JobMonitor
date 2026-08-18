from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.application.dto.miniapp.onboarding import (
    OnboardingDraftRequest,
    OnboardingStateResponse,
)
from app.application.services.onboarding_service import (
    InvalidOnboardingDraftError,
    OnboardingService,
    OnboardingUserNotFoundError,
)
from app.domain.user.entities import User
from app.telegram.miniapp.deps import get_current_user, get_onboarding_service

ONBOARDING_PREFIX = "/miniapp/api/onboarding"

router = APIRouter(prefix=ONBOARDING_PREFIX, tags=["onboarding"])


@router.get("", response_model=OnboardingStateResponse)
async def get_onboarding_state(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingStateResponse:
    return await _run(service.get_state(user.tg_id.value))


@router.patch("/draft", response_model=OnboardingStateResponse)
async def save_onboarding_draft(
    payload: OnboardingDraftRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingStateResponse:
    return await _run(service.save_draft(user.tg_id.value, payload))


@router.post("/complete", response_model=OnboardingStateResponse)
async def complete_onboarding(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingStateResponse:
    return await _run(service.complete(user.tg_id.value))


async def _run(operation: Awaitable[OnboardingStateResponse]) -> OnboardingStateResponse:
    try:
        return await operation
    except OnboardingUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Пользователь не найден.") from exc
    except InvalidOnboardingDraftError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
