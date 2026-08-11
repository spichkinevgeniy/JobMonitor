# ruff: noqa: T201

from __future__ import annotations

import argparse
import os
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPOSITORY_ROOT / "frontend"
BACKEND_URL = "http://127.0.0.1:8081"
FRONTEND_URL = "http://127.0.0.1:5173"
DASHBOARD_URL = "http://127.0.0.1:5174"
TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)


class DevEnvironmentError(RuntimeError):
    pass


@dataclass(slots=True)
class ManagedProcess:
    name: str
    process: subprocess.Popen[str]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the JobMonitor local Mini App stack")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="start DB, backend and frontend without a tunnel or Telegram bot",
    )
    parser.add_argument(
        "--with-scraper",
        action="store_true",
        help="start the Telegram bot together with the Telethon scraper",
    )
    parser.add_argument(
        "--public-url",
        default="",
        help="use an already running tunnel (ngrok and similar) instead of cloudflared",
    )
    args = parser.parse_args(argv)
    if args.public_url and args.browser:
        parser.error("--public-url and --browser cannot be used together")
    if args.browser and args.with_scraper:
        parser.error("--browser and --with-scraper cannot be used together")
    return args


def extract_tunnel_url(line: str) -> str | None:
    match = TUNNEL_URL_PATTERN.search(line)
    return match.group(0).rstrip("/") if match else None


def build_bot_environment(public_origin: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["MINI_APP_BASE_URL"] = public_origin.rstrip("/")
    return environment


def find_cloudflared() -> str | None:
    configured = os.environ.get("JOBMONITOR_CLOUDFLARED", "").strip()
    if configured:
        path = Path(configured).expanduser()
        return str(path) if path.is_file() else None

    executable = shutil.which("cloudflared")
    if executable:
        return executable

    windows_dev_binary = Path(tempfile.gettempdir()) / "jobmonitor-cloudflared.exe"
    if windows_dev_binary.is_file():
        return str(windows_dev_binary)
    return None


def _find_required_tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise DevEnvironmentError(f"Required tool is not available on PATH: {name}")
    return executable


def _run_checked(label: str, command: list[str], *, cwd: Path = REPOSITORY_ROOT) -> None:
    print(f"[dev] {label}...")
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        print(f"[dev] {label}: ready")
        return
    details = (result.stderr or result.stdout).strip()
    if details:
        print(details)
    raise DevEnvironmentError(f"{label} failed with exit code {result.returncode}")


def _start_process(
    name: str,
    command: list[str],
    *,
    cwd: Path = REPOSITORY_ROOT,
    environment: dict[str, str] | None = None,
) -> ManagedProcess:
    print(f"[dev] Starting {name}...")
    if os.name == "nt":
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            start_new_session=True,
        )
    return ManagedProcess(name=name, process=process)


def _start_tunnel(command: list[str]) -> tuple[ManagedProcess, queue.Queue[str]]:
    print("[dev] Starting HTTPS tunnel...")
    if os.name == "nt":
        process = subprocess.Popen(
            command,
            cwd=REPOSITORY_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        process = subprocess.Popen(
            command,
            cwd=REPOSITORY_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )

    url_queue: queue.Queue[str] = queue.Queue(maxsize=1)
    threading.Thread(
        target=_consume_tunnel_output,
        args=(process, url_queue),
        name="cloudflared-output",
        daemon=True,
    ).start()
    return ManagedProcess(name="tunnel", process=process), url_queue


def _consume_tunnel_output(
    process: subprocess.Popen[str],
    url_queue: queue.Queue[str],
) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        cleaned = line.rstrip()
        if cleaned:
            print(f"[tunnel] {cleaned}")
        tunnel_url = extract_tunnel_url(cleaned)
        if tunnel_url is not None and url_queue.empty():
            url_queue.put(tunnel_url)


def _wait_for_tunnel(
    managed: ManagedProcess,
    url_queue: queue.Queue[str],
    timeout_seconds: float = 45,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if managed.process.poll() is not None:
            raise DevEnvironmentError(
                f"Tunnel exited before publishing a URL (exit {managed.process.returncode})"
            )
        try:
            return url_queue.get(timeout=0.25)
        except queue.Empty:
            continue
    raise DevEnvironmentError("Tunnel did not publish a URL before timeout")


def _wait_for_postgres(docker: str, timeout_seconds: float = 90) -> None:
    print("[dev] Waiting for PostgreSQL healthcheck...")
    deadline = time.monotonic() + timeout_seconds
    container_id = ""
    while time.monotonic() < deadline:
        result = subprocess.run(
            [docker, "compose", "ps", "-q", "db"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        container_id = result.stdout.strip()
        if container_id:
            break
        time.sleep(0.25)
    if not container_id:
        raise DevEnvironmentError("PostgreSQL container was not created")

    while time.monotonic() < deadline:
        result = subprocess.run(
            [docker, "inspect", "--format", "{{.State.Health.Status}}", container_id],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        status = result.stdout.strip().lower()
        if status == "healthy":
            print("[dev] PostgreSQL: healthy")
            return
        if status == "unhealthy":
            raise DevEnvironmentError("PostgreSQL healthcheck reported unhealthy")
        time.sleep(0.5)
    raise DevEnvironmentError("PostgreSQL did not become healthy before timeout")


def _wait_for_http(
    name: str,
    url: str,
    managed: ManagedProcess,
    timeout_seconds: float = 60,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        return_code = managed.process.poll()
        if return_code is not None:
            raise DevEnvironmentError(f"{name} exited during startup (exit {return_code})")
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status < 500:
                    print(f"[dev] {name}: ready")
                    return
        except (OSError, URLError):
            time.sleep(0.25)
    raise DevEnvironmentError(f"{name} did not become ready at {url}")


def _ensure_port_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            if port == 5173:
                raise DevEnvironmentError(
                    "Frontend port 5173 is already in use. "
                    "Stop the process/container using it and run dev again."
                ) from exc
            raise DevEnvironmentError(f"Local port {port} is already in use") from exc


def _stop_process(managed: ManagedProcess, timeout_seconds: float = 8) -> None:
    process = managed.process
    if process.poll() is not None:
        return
    print(f"[dev] Stopping {managed.name}...")
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            _signal_process_group(process.pid, signal.SIGTERM)
        process.wait(timeout=timeout_seconds)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            _signal_process_group(
                process.pid,
                getattr(signal, "SIGKILL", signal.SIGTERM),
            )
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


def _signal_process_group(process_id: int, shutdown_signal: signal.Signals) -> None:
    kill_process_group = getattr(os, "killpg")  # noqa: B009 - unavailable in Windows stubs
    kill_process_group(process_id, shutdown_signal)


def _validate_application_config(*, telegram: bool, scraper: bool) -> None:
    checks = [
        "from app.core.config import config",
        "assert config.POSTGRES_SERVER and config.POSTGRES_PORT > 0",
        "assert config.POSTGRES_USER and config.POSTGRES_DB",
    ]
    if telegram:
        checks.append(
            "assert ':' in config.BOT_TOKEN and not config.BOT_TOKEN.lower().startswith('your')"
        )
    if scraper:
        checks.extend(
            [
                "assert config.API_ID > 0",
                "assert config.API_HASH and not config.API_HASH.lower().startswith('your')",
                "assert config.OPENROUTER_API_KEY and not "
                "config.OPENROUTER_API_KEY.lower().startswith(('your', 'you_'))",
            ]
        )
    _run_checked("Application configuration", [sys.executable, "-c", "; ".join(checks)])


def _validate_prerequisites(args: argparse.Namespace) -> tuple[str, str, str | None]:
    if not (REPOSITORY_ROOT / ".env").is_file():
        raise DevEnvironmentError("Missing .env; copy .env.sample and fill required values")
    if not (FRONTEND_ROOT / "node_modules").is_dir():
        raise DevEnvironmentError("Frontend dependencies are missing; run `cd frontend && npm ci`")

    docker = _find_required_tool("docker")
    npm = _find_required_tool("npm")
    skip_tunnel = args.browser or bool(args.public_url)
    cloudflared = None if skip_tunnel else find_cloudflared()
    if not skip_tunnel and cloudflared is None:
        raise DevEnvironmentError(
            "cloudflared is required for Telegram mode; install it or set "
            "JOBMONITOR_CLOUDFLARED to the executable path"
        )

    _run_checked("Docker Compose", [docker, "compose", "version"])
    _run_checked("Docker Compose configuration", [docker, "compose", "config", "--quiet"])
    _run_checked("npm", [npm, "--version"])
    _validate_application_config(telegram=not args.browser, scraper=args.with_scraper)
    if cloudflared is not None:
        _run_checked("cloudflared", [cloudflared, "--version"])
    return docker, npm, cloudflared


def _monitor(processes: list[ManagedProcess]) -> None:
    print("[dev] Environment is running. Press Ctrl+C to stop local processes.")
    while True:
        for managed in processes:
            return_code = managed.process.poll()
            if return_code is not None:
                raise DevEnvironmentError(
                    f"{managed.name} exited unexpectedly with code {return_code}"
                )
        time.sleep(0.5)


def run(args: argparse.Namespace) -> None:
    docker, npm, cloudflared = _validate_prerequisites(args)
    _ensure_port_available(8081)
    _ensure_port_available(5173)
    _ensure_port_available(5174)

    _run_checked("PostgreSQL container", [docker, "compose", "up", "-d", "db"])
    _wait_for_postgres(docker)
    _run_checked(
        "Database migrations",
        [sys.executable, "-m", "alembic", "upgrade", "head"],
    )

    processes: list[ManagedProcess] = []
    try:
        backend = _start_process(
            "backend",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.telegram.miniapp.app:app",
                "--reload",
                "--host",
                "127.0.0.1",
                "--port",
                "8081",
            ],
        )
        processes.append(backend)
        _wait_for_http("backend", f"{BACKEND_URL}/openapi.json", backend)

        dashboard = _start_process(
            "dashboard frontend",
            [npm, "run", "dev:dashboard"],
            cwd=FRONTEND_ROOT,
        )
        processes.append(dashboard)
        _wait_for_http(
            "dashboard frontend",
            f"{DASHBOARD_URL}/miniapp/dashboard/",
            dashboard,
        )

        frontend = _start_process(
            "frontend",
            [npm, "run", "dev:shell"],
            cwd=FRONTEND_ROOT,
        )
        processes.append(frontend)
        _wait_for_http("frontend", f"{FRONTEND_URL}/miniapp/react/", frontend)
        print(f"[dev] Frontend local URL: {FRONTEND_URL}/miniapp/react/")
        print(f"[dev] Dashboard local URL: {DASHBOARD_URL}/miniapp/dashboard/")

        if not args.browser:
            if args.public_url:
                public_origin = args.public_url.rstrip("/")
            else:
                public_origin = _open_cloudflared_tunnel(cloudflared, processes)
            public_miniapp_url = f"{public_origin}/miniapp/react/"
            print(f"[dev] Telegram Mini App URL: {public_miniapp_url}")

            bot_command = [sys.executable, "-m", "app.bot_main"]
            if args.with_scraper:
                bot_command.append("--with-scraper")
            bot = _start_process(
                "bot + scraper" if args.with_scraper else "bot",
                bot_command,
                environment=build_bot_environment(public_origin),
            )
            processes.append(bot)

        _monitor(processes)
    finally:
        for managed in reversed(processes):
            _stop_process(managed)
        print("[dev] Local processes stopped; PostgreSQL data volume was preserved")


def _open_cloudflared_tunnel(cloudflared: str | None, processes: list[ManagedProcess]) -> str:
    assert cloudflared is not None
    tunnel, url_queue = _start_tunnel(
        [cloudflared, "tunnel", "--url", FRONTEND_URL, "--no-autoupdate"]
    )
    processes.append(tunnel)
    return _wait_for_tunnel(tunnel, url_queue)


def main() -> int:
    args = parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        return 130
    except DevEnvironmentError as exc:
        print(f"[dev] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
