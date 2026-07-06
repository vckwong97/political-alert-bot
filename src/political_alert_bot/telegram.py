from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from political_alert_bot.matcher import Alert


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str


def load_telegram_config() -> TelegramConfig | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return None
    return TelegramConfig(bot_token=token, chat_id=chat_id)


def send_alert(config: TelegramConfig, alert: Alert) -> None:
    send_text(config, format_alert(alert), disable_web_page_preview=False)


def send_text(config: TelegramConfig, text: str, disable_web_page_preview: bool = True) -> None:
    url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": config.chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        },
        timeout=20,
    )
    response.raise_for_status()


def format_alert(alert: Alert) -> str:
    tickers = ", ".join(alert.tickers[:18]) or "n/a"
    sectors = ", ".join(alert.sectors) or "n/a"
    keywords = ", ".join(alert.matched_keywords[:12]) or "n/a"
    parts = [
        "NEW GOVERNMENT MARKET EVENT",
        "",
        f"Source: {alert.source}",
        f"Score: {alert.score}/100",
        f"Published: {alert.published_at}",
        f"Sectors: {sectors}",
        f"Tickers: {tickers}",
        f"Matched: {keywords}",
        "",
        alert.title,
    ]
    if alert.summary:
        parts.extend(["", alert.summary])
    if alert.link:
        parts.extend(["", alert.link])
    return "\n".join(parts)
