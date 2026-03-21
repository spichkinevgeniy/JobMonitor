from app.core.config import config
from app.infrastructure.telegram.miniapp_server import build_miniapp_server


def test_build_miniapp_server_enables_proxy_headers() -> None:
    server = build_miniapp_server()

    assert server.config.host == config.MINI_APP_SERVER_HOST
    assert server.config.port == config.MINI_APP_SERVER_PORT
    assert server.config.proxy_headers is True
    assert server.config.forwarded_allow_ips == "*"
