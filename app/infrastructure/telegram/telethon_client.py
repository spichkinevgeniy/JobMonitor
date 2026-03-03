from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneNumberInvalidError, SessionPasswordNeededError

from app.core.config import config
from app.core.logger import get_app_logger

logger = get_app_logger(__name__)


class TelethonClientProvider:
    _QR_REFRESH_SECONDS = 10

    def __init__(self, session_name: str | None = None) -> None:
        self._session_name = session_name or "data/job_monitor"
        self._client = TelegramClient(self._session_name, config.API_ID, config.API_HASH)

    @property
    def client(self) -> TelegramClient:
        return self._client

    async def start(self) -> TelegramClient:
        self._ensure_session_dir()
        await self._ensure_authorized()
        return self._client

    async def stop(self) -> None:
        if self._client.is_connected():
            await self._client.disconnect()

    def _ensure_session_dir(self) -> None:
        Path(self._session_name).parent.mkdir(parents=True, exist_ok=True)

    async def _ensure_authorized(self) -> None:
        if not self._client.is_connected():
            await self._client.connect()

        if await self._client.is_user_authorized():
            logger.info("Telethon session already authorized.")
            return

        login_mode = (config.TELETHON_LOGIN_MODE or "qr").lower()
        if login_mode == "phone":
            if not config.TELEGRAM_PHONE:
                raise RuntimeError("TELEGRAM_PHONE is required for phone login mode")
            try:
                await self._client.start(phone=config.TELEGRAM_PHONE)
                return
            except PhoneNumberInvalidError:
                logger.error("Invalid phone format. Use +79123456789")
                raise
            except FloodWaitError as exc:
                logger.error("Telegram flood wait: %ss", exc.seconds)
                raise

        while not await self._client.is_user_authorized():
            qr_login = await self._client.qr_login()
            self._log_qr(qr_login.url)
            while True:
                try:
                    await qr_login.wait(timeout=self._QR_REFRESH_SECONDS)
                    break
                except TimeoutError:
                    logger.warning("QR timed out, generating a new one...")
                    await qr_login.recreate()
                    self._log_qr(qr_login.url)
                except SessionPasswordNeededError as err:
                    if not config.TELEGRAM_2FA_PASSWORD:
                        raise RuntimeError(
                            "2FA is enabled. Set TELEGRAM_2FA_PASSWORD in .env"
                        ) from err
                    await self._client.sign_in(password=config.TELEGRAM_2FA_PASSWORD)
                    break

    def _log_qr(self, url: str) -> None:
        logger.info("Open this link in Telegram app to confirm login: %s", url)
        self._print_qr_to_terminal(url)

    @staticmethod
    def _print_qr_to_terminal(url: str) -> None:
        try:
            import qrcode
        except ImportError:
            logger.warning("Install 'qrcode': pip install qrcode")
            return
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        print("\nScan this QR in Telegram -> Settings -> Devices -> Link Desktop Device:\n")
        qr.print_ascii(invert=True)
        print()
