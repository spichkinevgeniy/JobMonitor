from types import SimpleNamespace

import pytest

from scripts import dev


def test_parse_browser_mode() -> None:
    args = dev.parse_args(["--browser"])

    assert args.browser is True
    assert args.with_scraper is False


def test_browser_and_scraper_modes_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        dev.parse_args(["--browser", "--with-scraper"])


def test_extract_tunnel_url_ignores_unrelated_cloudflared_output() -> None:
    assert dev.extract_tunnel_url("INF Requesting new quick Tunnel") is None
    assert (
        dev.extract_tunnel_url("INF +https://job-monitor-test.trycloudflare.com ready")
        == "https://job-monitor-test.trycloudflare.com"
    )


def test_bot_environment_receives_tunnel_without_mutating_parent(monkeypatch) -> None:
    monkeypatch.setenv("MINI_APP_BASE_URL", "https://production.example")

    environment = dev.build_bot_environment("https://local.trycloudflare.com/")

    assert environment["MINI_APP_BASE_URL"] == "https://local.trycloudflare.com"
    assert dev.os.environ["MINI_APP_BASE_URL"] == "https://production.example"


def test_configured_cloudflared_path_is_supported(monkeypatch) -> None:
    executable = dev.Path("C:/tools/cloudflared.exe")
    monkeypatch.setenv("JOBMONITOR_CLOUDFLARED", str(executable))
    monkeypatch.setattr(dev.Path, "is_file", lambda path: path == executable)

    assert dev.find_cloudflared() == str(executable)


def test_postgres_wait_uses_container_healthcheck(monkeypatch) -> None:
    results = iter(
        [
            SimpleNamespace(stdout="container-id\n", returncode=0),
            SimpleNamespace(stdout="healthy\n", returncode=0),
        ]
    )
    commands: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        commands.append(command)
        return next(results)

    monkeypatch.setattr(dev.subprocess, "run", fake_run)

    dev._wait_for_postgres("docker", timeout_seconds=1)

    assert commands[0] == ["docker", "compose", "ps", "-q", "db"]
    assert commands[1] == [
        "docker",
        "inspect",
        "--format",
        "{{.State.Health.Status}}",
        "container-id",
    ]


def test_postgres_unhealthy_fails_fast(monkeypatch) -> None:
    results = iter(
        [
            SimpleNamespace(stdout="container-id\n", returncode=0),
            SimpleNamespace(stdout="unhealthy\n", returncode=0),
        ]
    )
    monkeypatch.setattr(dev.subprocess, "run", lambda *_args, **_kwargs: next(results))

    with pytest.raises(dev.DevEnvironmentError, match="unhealthy"):
        dev._wait_for_postgres("docker", timeout_seconds=1)


def test_frontend_port_collision_fails_with_actionable_error(monkeypatch) -> None:
    class _OccupiedSocket:
        def __enter__(self) -> "_OccupiedSocket":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def bind(self, _address: tuple[str, int]) -> None:
            raise OSError("address already in use")

    monkeypatch.setattr(dev.socket, "socket", lambda *_args: _OccupiedSocket())

    with pytest.raises(
        dev.DevEnvironmentError,
        match=(
            "Frontend port 5173 is already in use. "
            "Stop the process/container using it and run dev again."
        ),
    ):
        dev._ensure_port_available(5173)


def test_free_frontend_port_passes_preflight(monkeypatch) -> None:
    bound_addresses: list[tuple[str, int]] = []

    class _FreeSocket:
        def __enter__(self) -> "_FreeSocket":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def bind(self, address: tuple[str, int]) -> None:
            bound_addresses.append(address)

    monkeypatch.setattr(dev.socket, "socket", lambda *_args: _FreeSocket())

    dev._ensure_port_available(5173)

    assert bound_addresses == [("127.0.0.1", 5173)]


def test_free_dashboard_port_passes_preflight(monkeypatch) -> None:
    bound_addresses: list[tuple[str, int]] = []

    class _FreeSocket:
        def __enter__(self) -> "_FreeSocket":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def bind(self, address: tuple[str, int]) -> None:
            bound_addresses.append(address)

    monkeypatch.setattr(dev.socket, "socket", lambda *_args: _FreeSocket())

    dev._ensure_port_available(5174)

    assert bound_addresses == [("127.0.0.1", 5174)]


def test_port_collision_stops_run_before_starting_services(monkeypatch) -> None:
    args = dev.parse_args(["--browser"])
    started_commands: list[list[str]] = []

    def ensure_port(port: int) -> None:
        if port == 5173:
            raise dev.DevEnvironmentError("Frontend port 5173 is already in use.")

    monkeypatch.setattr(
        dev,
        "_validate_prerequisites",
        lambda _args: ("docker", "npm", None),
    )
    monkeypatch.setattr(dev, "_ensure_port_available", ensure_port)
    monkeypatch.setattr(
        dev,
        "_run_checked",
        lambda _label, command, **_kwargs: started_commands.append(command),
    )

    with pytest.raises(dev.DevEnvironmentError, match="Frontend port 5173"):
        dev.run(args)

    assert started_commands == []
