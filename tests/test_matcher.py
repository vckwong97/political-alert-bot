from datetime import datetime, timezone

from political_alert_bot.config import SectorRule
from political_alert_bot.feeds import FeedItem
from political_alert_bot.matcher import match_item


def test_match_item_maps_keywords_to_tickers() -> None:
    item = FeedItem(
        id="white_house:1",
        source_id="white_house",
        source_name="White House",
        source_importance=5,
        title="New semiconductor export control announcement",
        link="https://example.com",
        summary="The action affects advanced AI chip exports to China.",
        published_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
    )
    rules = [
        SectorRule(
            name="semiconductors",
            tickers=["NVDA", "AMD"],
            keywords=["semiconductor", "ai chip", "export control"],
        )
    ]

    alert = match_item(item, rules, min_score=1)

    assert alert is not None
    assert alert.tickers == ["AMD", "NVDA"]
    assert alert.sectors == ["semiconductors"]
    assert "export control" in alert.matched_keywords
    assert alert.score >= 50


def test_match_item_ignores_low_score() -> None:
    item = FeedItem(
        id="source:1",
        source_id="source",
        source_name="Low Importance",
        source_importance=1,
        title="Bank rule update",
        link="https://example.com",
        summary="Bank capital requirements changed.",
        published_at=None,
    )
    rules = [SectorRule(name="banks", tickers=["JPM"], keywords=["bank"])]

    assert match_item(item, rules, min_score=90) is None
