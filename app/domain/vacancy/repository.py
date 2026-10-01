from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.vacancy.entities import DispatchedVacancy, DispatchMatch, Vacancy
from app.domain.vacancy.market import MarketAggregates
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

    async def find_for_specializations_since(
        self,
        specializations: set[str],
        since: datetime,
    ) -> list[Vacancy]: ...

    async def find_dispatched_for_user(
        self, user_tg_id: int, limit: int | None = None
    ) -> list[DispatchedVacancy]: ...

    async def count_dispatched_for_user(self, user_tg_id: int) -> tuple[int, datetime | None]: ...

    async def count_dispatches_between(
        self, user_tg_id: int, since: datetime, until: datetime
    ) -> tuple[int, int]: ...

    async def get_dispatch_match(
        self, vacancy_id: VacancyId, user_tg_id: int
    ) -> DispatchMatch | None: ...

    async def reject_dispatch(
        self, vacancy_id: VacancyId, user_tg_id: int, at: datetime
    ) -> None: ...

    async def clear_dispatch_feedback(self, vacancy_id: VacancyId, user_tg_id: int) -> None: ...

    async def salary_median(
        self,
        specialization: str,
        grade: str | None,
        since: datetime,
        until: datetime,
    ) -> tuple[int | None, int]: ...

    async def market_aggregates(
        self, counts_since: datetime, salary_since: datetime
    ) -> MarketAggregates: ...

    async def exists_by_content_hash(self, content_hash: ContentHash) -> bool: ...

    async def add(self, vacancy: Vacancy) -> None: ...

    async def update(self, vacancy: Vacancy) -> None: ...

    async def upsert(self, vacancy: Vacancy) -> None: ...
