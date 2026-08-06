from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.vacancy.entities import DispatchedVacancy, Vacancy
from app.domain.vacancy.value_objects import ContentHash, VacancyId


@runtime_checkable
class IVacancyRepository(Protocol):
    async def get_by_id(self, vacancy_id: VacancyId) -> Vacancy | None: ...

    async def find_for_profile_since(
        self,
        specializations: set[str],
        skills: set[str],
        since: datetime,
    ) -> list[Vacancy]: ...

    async def find_dispatched_for_user(
        self, user_tg_id: int, limit: int | None = None
    ) -> list[DispatchedVacancy]: ...

    async def count_dispatched_for_user(self, user_tg_id: int) -> tuple[int, datetime | None]: ...

    async def get_by_content_hash(self, content_hash: ContentHash) -> Vacancy | None: ...

    async def exists_by_content_hash(self, content_hash: ContentHash) -> bool: ...

    async def add(self, vacancy: Vacancy) -> None: ...

    async def update(self, vacancy: Vacancy) -> None: ...

    async def upsert(self, vacancy: Vacancy) -> None: ...
