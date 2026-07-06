from political_alert_bot.telegram_test import build_test_message


def test_build_test_message_contains_delivery_status() -> None:
    message = build_test_message("2026-07-07T00:00:00+00:00")

    assert "TRADING SIGNAL BOT TEST" in message
    assert "Telegram delivery is working." in message
    assert "2026-07-07T00:00:00+00:00" in message
