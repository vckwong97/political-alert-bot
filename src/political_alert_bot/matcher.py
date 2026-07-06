from __future__ import annotations

from dataclasses import dataclass

from political_alert_bot.config import SectorRule
from political_alert_bot.feeds import FeedItem


@dataclass(frozen=True)
class Alert:
    id: str
    source: str
    title: str
    link: str
    published_at: str
    sectors: list[str]
    tickers: list[str]
    matched_keywords: list[str]
    score: int
    summary: str


def match_item(item: FeedItem, rules: list[SectorRule], min_score: int) -> Alert | None:
    searchable = f"{item.title} {item.summary}".lower()
    sectors: list[str] = []
    tickers: list[str] = []
    keywords: list[str] = []

    for rule in rules:
        matched = [keyword for keyword in rule.keywords if keyword in searchable]
        if not matched:
            continue
        sectors.append(rule.name)
        tickers.extend(rule.tickers)
        keywords.extend(matched)

    if not sectors:
        return None

    unique_tickers = sorted(set(tickers))
    unique_keywords = sorted(set(keywords))
    score = _score(item.source_importance, len(sectors), len(unique_keywords))
    if score < min_score:
        return None

    published = item.published_at.isoformat() if item.published_at else "unknown"
    return Alert(
        id=item.id,
        source=item.source_name,
        title=item.title,
        link=item.link,
        published_at=published,
        sectors=sorted(set(sectors)),
        tickers=unique_tickers,
        matched_keywords=unique_keywords,
        score=score,
        summary=item.summary[:350],
    )


def _score(source_importance: int, sector_count: int, keyword_count: int) -> int:
    raw = (source_importance * 12) + (sector_count * 10) + min(keyword_count, 8) * 4
    return max(0, min(raw, 100))
