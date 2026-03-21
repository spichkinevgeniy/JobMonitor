from dataclasses import dataclass
from uuid import uuid4

from app.application.services.matcher_service import MatcherService
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.vacancy.entities import Vacancy


@dataclass
class _ObservabilitySpy:
    seen: list[tuple[str, int]]

    def observe_skill_match(self, skill: str, count: int = 1) -> None:
        self.seen.append((skill, count))


class _NotificationDummy:
    async def dispatch_vacancy(self, **_: object) -> None:
        return None


class _UnitOfWorkDummy:
    pass


def test_observe_skill_matches_tracks_shared_skills() -> None:
    observability = _ObservabilitySpy(seen=[])
    service = MatcherService(
        uow=_UnitOfWorkDummy(),  # type: ignore[arg-type]
        notification_service=_NotificationDummy(),  # type: ignore[arg-type]
        observability=observability,  # type: ignore[arg-type]
    )
    vacancy = Vacancy.create(
        vacancy_id=uuid4(),
        text="Frontend engineer with React and Vue",
        specializations_raw=["Frontend"],
        skills_raw=["React", "Vue"],
        mirror_chat_id=1,
        mirror_message_id=1,
        work_format=WorkFormat.REMOTE,
    )
    user = User.create(
        tg_id=1,
        cv_specializations_raw=["Frontend"],
        cv_skills_raw=["Vue", "Python"],
    )

    service._observe_skill_matches(vacancy=vacancy, user=user)

    assert observability.seen == [("vue", 1)]
