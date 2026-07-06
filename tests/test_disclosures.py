from datetime import date
from pathlib import Path

from political_alert_bot.disclosures import TradeSource, collect_trade_alerts
from political_alert_bot.state import SeenState
from political_alert_bot.trades import PoliticalTrade, TradeHistoryStore


def test_collect_trade_alerts_returns_new_trade_message(monkeypatch, tmp_path: Path) -> None:
    state = SeenState(tmp_path / "seen_alerts.json")
    history = TradeHistoryStore(tmp_path / "trade_history.json")
    history.upsert(
        PoliticalTrade(
            id="old-nvda-buy",
            person="Alice Member",
            office="House",
            party="D",
            state="CA",
            action="Buy",
            ticker="NVDA",
            company="NVIDIA Corp.",
            amount="$15,001-$50,000",
            trade_date="2026-06-01",
            disclosure_date="2026-06-12",
            source_url="https://example.com/old",
        )
    )

    today = date.today().strftime("%Y-%m-%d")

    def fake_fetch(_url: str) -> list[dict[str, str]]:
        return [
            {
                "representative": "Bob Senator",
                "type": "Purchase",
                "ticker": "NVDA",
                "asset_description": "NVIDIA Corp.",
                "amount": "$1,001-$15,000",
                "transaction_date": today,
                "disclosure_date": today,
                "source_url": "https://example.com/new",
            }
        ]

    monkeypatch.setattr("political_alert_bot.disclosures._fetch_records", fake_fetch)

    alerts, added_to_history = collect_trade_alerts(
        state=state,
        history=history,
        lookback_hours=96,
        max_alerts=5,
        include_senate=False,
        include_house=True,
        sources=[TradeSource(name="House", url="https://example.com", default_office="House")],
    )

    assert added_to_history == 1
    assert len(alerts) == 1
    assert "NEW POLITICIAN TRADE DISCLOSURE" in alerts[0].message
    assert "Alice Member also bought NVDA" in alerts[0].message


def test_collect_trade_alerts_skips_old_disclosures(monkeypatch, tmp_path: Path) -> None:
    state = SeenState(tmp_path / "seen_alerts.json")
    history = TradeHistoryStore(tmp_path / "trade_history.json")

    def fake_fetch(_url: str) -> list[dict[str, str]]:
        return [
            {
                "representative": "Old Member",
                "type": "Purchase",
                "ticker": "AAPL",
                "asset_description": "Apple Inc.",
                "amount": "$1,001-$15,000",
                "transaction_date": "2025-01-01",
                "disclosure_date": "2025-01-01",
                "source_url": "https://example.com/old",
            }
        ]

    monkeypatch.setattr("political_alert_bot.disclosures._fetch_records", fake_fetch)

    alerts, added_to_history = collect_trade_alerts(
        state=state,
        history=history,
        lookback_hours=24,
        max_alerts=5,
        include_senate=False,
        include_house=True,
        sources=[TradeSource(name="House", url="https://example.com", default_office="House")],
    )

    assert alerts == []
    assert added_to_history == 0
