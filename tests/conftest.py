import os

# Ensure test collection does not depend on a private .env file or CI secrets.
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("API_ID", "1")
os.environ.setdefault("API_HASH", "test-api-hash")
os.environ.setdefault("BOT_TOKEN", "123456:test-bot-token")
os.environ.setdefault("MINI_APP_SERVER_HOST", "127.0.0.1")
os.environ.setdefault("MINI_APP_SERVER_PORT", "8081")
os.environ.setdefault("MIRROR_CHANNEL", "-1001234567890")
os.environ.setdefault("CHANNELS_MAP_PATH", "channels_map.json")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-api-key")
os.environ.setdefault("LOGFIRE_ENABLED", "false")
os.environ.setdefault("LOGFIRE_SERVICE_NAME", "smartjobmonitor-tests")
