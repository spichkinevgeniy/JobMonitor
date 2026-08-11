from collections.abc import Generator
from contextlib import contextmanager

from uvicorn import Config, Server

from app.core.config import config


class MiniAppServer(Server):
    @contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        yield


def build_miniapp_server(*, host: str | None = None, port: int | None = None) -> MiniAppServer:
    server_config = Config(
        app="app.telegram.miniapp.app:app",
        host=config.MINI_APP_SERVER_HOST if host is None else host,
        port=config.MINI_APP_SERVER_PORT if port is None else port,
        # Вебсокетов в мини-аппе нет, и nginx апгрейд не проксирует. Пакет
        # websockets приезжал транзитивно и ушёл вместе с лишними
        # зависимостями pydantic-ai — включать его обратно незачем.
        ws="none",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    return MiniAppServer(server_config)


async def run_miniapp_server(server: MiniAppServer | None = None) -> None:
    miniapp_server = server or build_miniapp_server()
    await miniapp_server.serve()
