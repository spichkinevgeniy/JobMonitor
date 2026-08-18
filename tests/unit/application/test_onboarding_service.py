from copy import deepcopy
from types import TracebackType

import pytest
from pydantic import TypeAdapter

from app.application.dto.miniapp import OnboardingDraftRequest
from app.application.services.onboarding_service import (
    InvalidOnboardingDraftError,
    OnboardingService,
)
from app.domain.shared import Grade, WorkFormat
from app.domain.user.entities import User
from app.domain.user.onboarding import OnboardingLevel, OnboardingStep
from app.domain.user.value_objects import FilterMode, LevelFilterMode, UserId
from app.telegram.bot.views.profile import build_search_profile_text
from app.telegram.bot.views.settings import build_settings_menu_view


class _UserRepositoryFake:
    def __init__(self, user: User) -> None:
        self.user = user
        self.fail_update = False
        self.update_count = 0

    async def get_by_tg_id(self, tg_id: UserId) -> User | None:
        return self.user if self.user.tg_id == tg_id else None

    async def get_by_tg_id_for_update(self, tg_id: UserId) -> User | None:
        return await self.get_by_tg_id(tg_id)

    async def update(self, user: User) -> None:
        self.update_count += 1
        if self.fail_update:
            raise RuntimeError("database failure")
        self.user = user


class _UserUnitOfWorkFake:
    def __init__(self, repository: _UserRepositoryFake) -> None:
        self.users = repository
        self._snapshot: User | None = None

    async def __aenter__(self) -> "_UserUnitOfWorkFake":
        self._snapshot = deepcopy(self.users.user)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None and self._snapshot is not None:
            self.users.user = self._snapshot

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        if self._snapshot is not None:
            self.users.user = self._snapshot


_adapter = TypeAdapter(OnboardingDraftRequest)


def _request(payload: dict[str, object]) -> OnboardingDraftRequest:
    return _adapter.validate_python(payload)


def _service(user: User) -> tuple[OnboardingService, _UserRepositoryFake]:
    repository = _UserRepositoryFake(user)
    service = OnboardingService(_UserUnitOfWorkFake(repository))  # type: ignore[arg-type]
    return service, repository


async def _save_complete_draft(service: OnboardingService) -> None:
    await service.save_draft(
        1,
        _request(
            {
                "step": "SPECIALTY",
                "navigate_to": "WORK_FORMAT",
                "data": {
                    "specializations": ["UI/UX & Product Design", "Frontend"],
                    "skills": ["JavaScript", "Docker"],
                },
            }
        ),
    )
    await service.save_draft(
        1,
        _request(
            {
                "step": "WORK_FORMAT",
                "navigate_to": "SALARY",
                "data": {"work_formats": ["REMOTE", "HYBRID"]},
            }
        ),
    )
    await service.save_draft(
        1,
        _request(
            {
                "step": "SALARY",
                "navigate_to": "LEVEL",
                "data": {"mode": "FROM", "amount_rub": 150000},
            }
        ),
    )
    await service.save_draft(
        1,
        _request(
            {
                "step": "LEVEL",
                "navigate_to": "LEVEL",
                "data": {"level": "JUNIOR_PLUS"},
            }
        ),
    )


@pytest.mark.asyncio
async def test_new_user_get_returns_empty_server_draft() -> None:
    service, _ = _service(User.create(tg_id=1))

    state = await service.get_state(1)

    assert state.completed is False
    assert state.current_step is OnboardingStep.SPECIALTY
    assert state.max_visited_step is OnboardingStep.SPECIALTY
    assert state.draft.specializations == []
    assert state.draft.specialty is None
    assert state.draft.work_formats is None


@pytest.mark.asyncio
async def test_each_patch_restores_full_draft_and_max_visited_never_decreases() -> None:
    service, _ = _service(User.create(tg_id=1))

    await _save_complete_draft(service)
    await service.save_draft(
        1,
        _request(
            {
                "step": "LEVEL",
                "navigate_to": "SPECIALTY",
                "data": {"level": "JUNIOR_PLUS"},
            }
        ),
    )
    state = await service.save_draft(
        1,
        _request(
            {
                "step": "SPECIALTY",
                "navigate_to": "WORK_FORMAT",
                "data": {
                    "specializations": ["Frontend", "Backend"],
                    "skills": ["React"],
                },
            }
        ),
    )

    assert state.current_step is OnboardingStep.WORK_FORMAT
    assert state.max_visited_step is OnboardingStep.LEVEL
    assert state.draft.specializations == ["Backend", "Frontend"]
    assert state.draft.specialty == "Backend"
    assert state.draft.work_formats == ["HYBRID", "REMOTE"]
    assert state.draft.salary is not None
    assert state.draft.salary.amount_rub == 150000
    assert state.draft.level is OnboardingLevel.JUNIOR_PLUS


@pytest.mark.asyncio
async def test_navigation_cannot_skip_unvisited_steps() -> None:
    service, _ = _service(User.create(tg_id=1))

    with pytest.raises(InvalidOnboardingDraftError, match="Cannot skip"):
        await service.save_draft(
            1,
            _request(
                {
                    "step": "SPECIALTY",
                    "navigate_to": "LEVEL",
                    "data": {"specializations": ["Frontend"], "skills": []},
                }
            ),
        )


@pytest.mark.asyncio
async def test_navigation_only_patch_moves_backward_without_persisting_empty_step() -> None:
    service, _ = _service(User.create(tg_id=1))
    await service.save_draft(
        1,
        _request(
            {
                "step": "SPECIALTY",
                "navigate_to": "WORK_FORMAT",
                "data": {"specializations": ["QA"], "skills": ["TypeScript"]},
            }
        ),
    )

    state = await service.save_draft(
        1,
        _request(
            {
                "step": "WORK_FORMAT",
                "navigate_to": "SPECIALTY",
                "data": None,
            }
        ),
    )
    restored = await service.get_state(1)

    assert state.current_step is OnboardingStep.SPECIALTY
    assert state.max_visited_step is OnboardingStep.WORK_FORMAT
    assert state.draft.specializations == ["QA"]
    assert state.draft.specialty == "QA"
    assert state.draft.skills == ["TypeScript"]
    assert state.draft.work_formats is None
    assert restored.current_step is OnboardingStep.SPECIALTY
    assert restored.max_visited_step is OnboardingStep.WORK_FORMAT


@pytest.mark.asyncio
async def test_navigation_only_patch_cannot_move_forward() -> None:
    service, _ = _service(User.create(tg_id=1))

    with pytest.raises(InvalidOnboardingDraftError, match="only allowed backward"):
        await service.save_draft(
            1,
            _request(
                {
                    "step": "SPECIALTY",
                    "navigate_to": "WORK_FORMAT",
                    "data": None,
                }
            ),
        )


@pytest.mark.asyncio
async def test_incomplete_complete_is_rejected_without_applying_filters() -> None:
    user = User.create(tg_id=1, cv_specializations_raw=["Backend"])
    service, repository = _service(user)
    await service.save_draft(
        1,
        _request(
            {
                "step": "SPECIALTY",
                "navigate_to": "WORK_FORMAT",
                "data": {
                    "specializations": ["UI/UX & Product Design"],
                    "skills": [],
                },
            }
        ),
    )

    with pytest.raises(InvalidOnboardingDraftError, match="incomplete"):
        await service.complete(1)

    assert {item.value for item in repository.user.cv_specializations.items} == {"Backend"}
    assert repository.user.onboarding_completed_at is None


@pytest.mark.asyncio
async def test_complete_applies_all_filters_and_junior_plus() -> None:
    service, repository = _service(User.create(tg_id=1))
    await _save_complete_draft(service)

    state = await service.complete(1)

    user = repository.user
    assert state.completed is True
    assert user.onboarding_draft is None
    assert {item.value for item in user.cv_specializations.items} == {
        "UI/UX & Product Design",
        "Frontend",
    }
    assert {item.value for item in user.cv_skills.items} == {"JavaScript", "Docker"}
    assert user.effective_work_formats.items == {WorkFormat.REMOTE, WorkFormat.HYBRID}
    assert user.cv_work_format is None
    assert user.filter_work_format_mode is FilterMode.SOFT
    assert user.cv_salary is not None and user.cv_salary.amount == 150000
    assert user.cv_grade is Grade.JUNIOR
    assert user.filter_grade_mode is LevelFilterMode.AT_LEAST
    assert "показываем этот уровень и выше" in build_search_profile_text(user)
    assert "от Junior" in build_settings_menu_view(user).level_label


@pytest.mark.asyncio
async def test_complete_is_idempotent() -> None:
    service, repository = _service(User.create(tg_id=1))
    await _save_complete_draft(service)
    first = await service.complete(1)
    update_count = repository.update_count

    second = await service.complete(1)

    assert second.completed_at == first.completed_at
    assert repository.update_count == update_count


@pytest.mark.asyncio
async def test_complete_rolls_back_when_persistence_fails() -> None:
    service, repository = _service(User.create(tg_id=1))
    await _save_complete_draft(service)
    repository.fail_update = True

    with pytest.raises(RuntimeError, match="database failure"):
        await service.complete(1)

    assert repository.user.onboarding_completed_at is None
    assert repository.user.onboarding_draft is not None
    assert repository.user.cv_grade is None
