"""Ссылка на исходный пост, включая форумы.

Проверено на проде: t.me/front_end_jobs/16740 не открывается,
t.me/front_end_jobs/2/16740 открывается. В форумах нужна тема.
"""

from uuid import uuid4

import pytest

from app.domain.shared.value_objects import WorkFormat
from app.domain.vacancy.entities import Vacancy


def _vacancy(channel: str | None, message_id: int | None, topic_id: int | None = None) -> Vacancy:
    return Vacancy.create(
        vacancy_id=uuid4(),
        text="Вакансия",
        specializations_raw=["Backend"],
        skills_raw=["Python"],
        mirror_chat_id=1,
        mirror_message_id=2,
        work_format=WorkFormat.REMOTE,
        source_channel=channel,
        source_message_id=message_id,
        source_topic_id=topic_id,
    )


class TestForum:
    def test_topic_goes_into_the_link(self) -> None:
        vacancy = _vacancy("@front_end_jobs", 16740, topic_id=2)

        assert vacancy.source_url == "https://t.me/front_end_jobs/2/16740"

    @pytest.mark.parametrize(
        ("channel", "topic", "message", "expected"),
        [
            ("@javascript_jobs", 25, 893757, "https://t.me/javascript_jobs/25/893757"),
            ("@fordev", 49, 57303, "https://t.me/fordev/49/57303"),
        ],
    )
    def test_real_prod_links(self, channel: str, topic: int, message: int, expected: str) -> None:
        """Ссылки, которые я проверил вручную на проде."""
        assert _vacancy(channel, message, topic_id=topic).source_url == expected


class TestPlainChannel:
    def test_without_topic_link_stays_two_part(self) -> None:
        assert _vacancy("@job_webdev", 3860).source_url == "https://t.me/job_webdev/3860"

    def test_no_link_without_channel(self) -> None:
        assert _vacancy(None, 123, topic_id=5).source_url is None

    def test_no_link_without_message(self) -> None:
        assert _vacancy("@job_webdev", None).source_url is None

    def test_no_link_for_private_channel(self) -> None:
        assert _vacancy("Закрытый канал", 123).source_url is None
