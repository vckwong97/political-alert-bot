from __future__ import annotations

from datetime import datetime, timezone

from political_alert_bot.telegram import load_telegram_config, send_text


def main() -> int:
    config = load_telegram_config()
    if config is None:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    sent_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    send_text(config, build_test_message(sent_at))
    print("Sent Telegram test message.")
    return 0


def build_test_message(sent_at: str) -> str:
    return "\n".join(
        [
            "TRADING SIGNAL BOT TEST",
            "",
            "Telegram delivery is working.",
            f"Sent at: {sent_at}",
            "",
            "Next real alerts will appear here when a monitored source matches.",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
