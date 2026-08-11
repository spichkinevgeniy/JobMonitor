from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.application.dto.miniapp.search_profile import SearchProfileResponse
from app.application.services.search_profile_service import (
    IncompleteSearchProfileError,
    SearchProfileService,
)
from app.domain.user.entities import User
from app.telegram.miniapp.deps import get_current_user, get_search_profile_service

router = APIRouter(prefix="/miniapp/api/search-profile", tags=["search-profile"])


@router.get("", response_model=SearchProfileResponse)
async def get_search_profile(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SearchProfileService, Depends(get_search_profile_service)],
) -> SearchProfileResponse:
    try:
        return service.get_profile(user)
    except IncompleteSearchProfileError as exc:
        raise HTTPException(
            status_code=409,
            detail="Профиль поиска ещё не завершён.",
        ) from exc
