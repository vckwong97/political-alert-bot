from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from re import sub
from typing import Any

import feedparser

from political_alert_bot.config import Source


@dataclass(frozen=True)
class FeedItem:
    id: str
    source_id: str
    source_name: str
    source_importance: int
    title: str
    link: str
    summary: str
    published_at: datetime | None


def fetch_source(source: Source, max_items: int = 10) -> list[FeedItem]:
    parsed = feedparser.parse(source.url)
    items: list[FeedItem] = []
    for entry in parsed.entries[:max_items]:
        title = _clean_text(str(entry.get("title", "")))
        link = str(entry.get("link", ""))
        summary = _clean_text(str(entry.get("summary", entry.get("description", ""))))
        published_at = _parse_date(entry)
        stable_id = _stable_id(source.id, entry, title, link)
        items.append(
            FeedItem(
                id=stable_id,
                source_id=source.id,
                source_name=source.name,
                source_importance=source.importance,
                title=title,
                link=link,
                summary=summary,
                published_at=published_at,
            )
        )
    return items


def _stable_id(source_id: str, entry: dict[str, Any], title: str, link: str) -> str:
    raw_id = str(entry.get("id", entry.get("guid", ""))).strip()
    basis = raw_id or link or title
    digest = sha256(f"{source_id}:{basis}".encode("utf-8")).hexdigest()[:24]
    return f"{source_id}:{digest}"


def _parse_date(entry: dict[str, Any]) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(str(value))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def _clean_text(value: str) -> str:
    no_tags = sub(r"<[^>]+>", " ", value)
    compact = sub(r"\s+", " ", unescape(no_tags)).strip()
    return compact
