"""Текст /help."""

from app.telegram.bot.views import SUPPORT_BOT_HANDLE, build_help_text


def test_tells_channel_owners_how_to_opt_out() -> None:
    """Владелец канала должен знать, куда написать, чтобы канал убрали."""
    text = build_help_text()

    assert "владелец канала" in text
    assert f"напишите в {SUPPORT_BOT_HANDLE}, уберём" in text
