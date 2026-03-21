import hashlib
import hmac
import json
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.core.config import config
from app.domain.shared import WorkFormat
from app.domain.user.entities import User
from app.domain.user.value_objects import FilterMode
from app.telegram.miniapp.app import build_miniapp_app
from app.telegram.miniapp.deps import get_user_service


class FakeUserService:
    def __init__(self, user: User | None = None) -> None:
        self.user = user
        self.specialty_result = True
        self.work_format_result = True
        self.salary_result = True
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        self.calls.append(("get_user_by_tg_id", {"tg_id": tg_id}))
        return self.user

    async def update_profile_specializations_and_skills(
        self,
        tg_id: int,
        specializations: list[str],
        skills: list[str],
    ) -> bool:
        self.calls.append(
            (
                "update_profile_specializations_and_skills",
                {
                    "tg_id": tg_id,
                    "specializations": specializations,
                    "skills": skills,
                },
            )
        )
        return self.specialty_result

    async def update_profile_work_format_filter(
        self,
        tg_id: int,
        work_format: WorkFormat | None,
        work_format_mode: FilterMode,
    ) -> bool:
        self.calls.append(
            (
                "update_profile_work_format_filter",
                {
                    "tg_id": tg_id,
                    "work_format": work_format,
                    "work_format_mode": work_format_mode,
                },
            )
        )
        return self.work_format_result

    async def update_profile_salary_filter(
        self,
        tg_id: int,
        salary_amount_rub: int | None,
        salary_mode: FilterMode,
    ) -> bool:
        self.calls.append(
            (
                "update_profile_salary_filter",
                {
                    "tg_id": tg_id,
                    "salary_amount_rub": salary_amount_rub,
                    "salary_mode": salary_mode,
                },
            )
        )
        return self.salary_result


def test_specialty_page_renders_domain_options() -> None:
    with TestClient(build_miniapp_app()) as client:
        response = client.get("/miniapp/specialty")

    assert response.status_code == 200
    assert "Настройка специальностей" in response.text
    assert "Добавьте или удалите нужные:" in response.text
    assert "Backend" in response.text
    assert "Frontend" in response.text
    assert "Python" in response.text
    assert "React" in response.text
    assert "Vue" in response.text


def test_specialty_page_uses_relative_asset_and_api_urls_under_proxy_headers() -> None:
    with TestClient(build_miniapp_app(), base_url="http://internal:8080") as client:
        response = client.get(
            "/miniapp/specialty",
            headers={
                "host": "example.ngrok-free.dev",
                "x-forwarded-proto": "https",
            },
        )

    assert response.status_code == 200
    assert 'href="/miniapp/static/css/app.css?v=' in response.text
    assert 'src="/miniapp/static/js/app.js?v=' in response.text
    assert 'data-save-url="/miniapp/api/specialty"' in response.text
    assert "http://example.ngrok-free.dev/miniapp/static" not in response.text
    assert "http://example.ngrok-free.dev/miniapp/api/" not in response.text


def test_format_page_renders_domain_work_format_options() -> None:
    with TestClient(build_miniapp_app()) as client:
        response = client.get("/miniapp/format")

    assert response.status_code == 200
    assert "ANY" in response.text
    assert "REMOTE" in response.text
    assert "HYBRID" in response.text
    assert "ONSITE" in response.text
    assert "UNDEFINED" not in response.text


def test_miniapp_index_redirects_to_relative_specialty_path() -> None:
    with TestClient(build_miniapp_app(), base_url="http://internal:8080") as client:
        response = client.get(
            "/miniapp",
            headers={
                "host": "example.ngrok-free.dev",
                "x-forwarded-proto": "https",
            },
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "/miniapp/specialty"


def test_read_specialty_returns_current_profile() -> None:
    with make_client(
        FakeUserService(
            build_user(
                cv_specializations_raw=["Frontend", "Backend"],
                cv_skills_raw=["React", "Python"],
            )
        )
    ) as (client, _service):
        response = client.get("/miniapp/api/specialty", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "specializations": ["Backend", "Frontend"],
        "skills": ["Python", "React"],
    }


def test_save_specialty_uses_transport_agnostic_service_method() -> None:
    with make_client(FakeUserService(build_user())) as (client, service):
        response = client.post(
            "/miniapp/api/specialty",
            json={
                "init_data": build_init_data(),
                "specializations": ["Backend"],
                "skills": ["Python", "React"],
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert service.calls[-1] == (
        "update_profile_specializations_and_skills",
        {
            "tg_id": 123,
            "specializations": ["Backend"],
            "skills": ["Python", "React"],
        },
    )


def test_read_format_returns_any_for_soft_filter() -> None:
    with make_client(FakeUserService(build_user())) as (client, _service):
        response = client.get("/miniapp/api/format", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"work_format_choice": "ANY"}


def test_save_format_updates_work_format_filter() -> None:
    with make_client(FakeUserService(build_user())) as (client, service):
        response = client.post(
            "/miniapp/api/format",
            json={
                "init_data": build_init_data(),
                "work_format_choice": "REMOTE",
            },
        )

    assert response.status_code == 200
    assert service.calls[-1] == (
        "update_profile_work_format_filter",
        {
            "tg_id": 123,
            "work_format": WorkFormat.REMOTE,
            "work_format_mode": FilterMode.STRICT,
        },
    )


def test_read_salary_returns_from_mode_and_amount() -> None:
    with make_client(
        FakeUserService(
            build_user(
                cv_salary_amount=250000,
                cv_salary_currency="RUB",
                filter_salary_mode=FilterMode.STRICT,
            )
        )
    ) as (client, _service):
        response = client.get("/miniapp/api/salary", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "salary_mode": "FROM",
        "salary_amount_rub": 250000,
    }


def test_save_salary_updates_salary_filter() -> None:
    with make_client(FakeUserService(build_user())) as (client, service):
        response = client.post(
            "/miniapp/api/salary",
            json={
                "init_data": build_init_data(),
                "salary_mode": "FROM",
                "salary_amount_rub": 250000,
            },
        )

    assert response.status_code == 200
    assert service.calls[-1] == (
        "update_profile_salary_filter",
        {
            "tg_id": 123,
            "salary_amount_rub": 250000,
            "salary_mode": FilterMode.STRICT,
        },
    )


def test_read_specialty_requires_valid_init_data() -> None:
    with make_client(FakeUserService(build_user())) as (client, _service):
        response = client.get("/miniapp/api/specialty")

    assert response.status_code == 401
    assert response.json() == {"detail": "Пустой initData."}


def test_save_format_returns_not_found_when_user_missing() -> None:
    service = FakeUserService(build_user())
    service.work_format_result = False

    with make_client(service) as (client, _service):
        response = client.post(
            "/miniapp/api/format",
            json={
                "init_data": build_init_data(),
                "work_format_choice": "REMOTE",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Пользователь не найден."}


def test_save_salary_rejects_invalid_from_amount() -> None:
    with make_client(FakeUserService(build_user())) as (client, _service):
        response = client.post(
            "/miniapp/api/salary",
            json={
                "init_data": build_init_data(),
                "salary_mode": "FROM",
                "salary_amount_rub": 0,
            },
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Укажите зарплату больше 0."}


class ClientContext:
    def __init__(self, service: FakeUserService) -> None:
        self.service = service
        self.app = build_miniapp_app()
        self.app.dependency_overrides[get_user_service] = lambda: service
        self.client = TestClient(self.app)

    def __enter__(self) -> tuple[TestClient, FakeUserService]:
        self.client.__enter__()
        return self.client, self.service

    def __exit__(self, exc_type, exc, tb) -> None:
        self.client.__exit__(exc_type, exc, tb)


def make_client(service: FakeUserService) -> ClientContext:
    return ClientContext(service)


def build_user(**kwargs: object) -> User:
    defaults: dict[str, object] = {
        "tg_id": 123,
        "username": "tester",
        "cv_specializations_raw": ["Backend"],
        "cv_skills_raw": ["Python"],
    }
    defaults.update(kwargs)
    return User.create(**defaults)


def auth_headers() -> dict[str, str]:
    return {"X-Telegram-Init-Data": build_init_data()}


def build_init_data() -> str:
    payload = {
        "auth_date": "1700000000",
        "user": json.dumps({"id": 123, "username": "tester"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(
        b"WebAppData",
        config.BOT_TOKEN.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)
