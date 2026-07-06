from pathlib import Path

from political_alert_bot.trades import PoliticalTrade, TradeHistoryStore, format_trade_alert


def test_trade_history_finds_apparent_holders(tmp_path: Path) -> None:
    store = TradeHistoryStore(tmp_path / "trade_history.json")
    store.upsert(
        PoliticalTrade(
            id="aapl-buy-a",
            person="Alice Member",
            office="House",
            party="D",
            state="CA",
            action="Buy",
            ticker="AAPL",
            company="Apple Inc.",
            amount="$15,001-$50,000",
            trade_date="2026-06-01",
            disclosure_date="2026-06-20",
            source_url="https://example.com/a",
        )
    )
    store.upsert(
        PoliticalTrade(
            id="aapl-buy-b",
            person="Bob Senator",
            office="Senate",
            party="R",
            state="TX",
            action="Purchase",
            ticker="AAPL",
            company="Apple Inc.",
            amount="$1,001-$15,000",
            trade_date="2026-06-05",
            disclosure_date="2026-06-22",
            source_url="https://example.com/b",
        )
    )
    store.upsert(
        PoliticalTrade(
            id="aapl-sell-a",
            person="Alice Member",
            office="House",
            party="D",
            state="CA",
            action="Sell",
            ticker="AAPL",
            company="Apple Inc.",
            amount="$15,001-$50,000",
            trade_date="2026-06-10",
            disclosure_date="2026-06-25",
            source_url="https://example.com/c",
        )
    )

    holders = store.apparent_holders("aapl")

    assert [holder.person for holder in holders] == ["Bob Senator"]


def test_format_trade_alert_includes_historical_comment(tmp_path: Path) -> None:
    store = TradeHistoryStore(tmp_path / "trade_history.json")
    previous_trade = PoliticalTrade(
        id="nvda-buy-previous",
        person="Carol Representative",
        office="House",
        party="D",
        state="NY",
        action="Buy",
        ticker="NVDA",
        company="NVIDIA Corp.",
        amount="$15,001-$50,000",
        trade_date="2026-06-01",
        disclosure_date="2026-06-15",
        source_url="https://example.com/previous",
    )
    new_trade = PoliticalTrade(
        id="nvda-buy-new",
        person="Dan Senator",
        office="Senate",
        party="I",
        state="VT",
        action="Buy",
        ticker="NVDA",
        company="NVIDIA Corp.",
        amount="$50,001-$100,000",
        trade_date="2026-06-20",
        disclosure_date="2026-07-06",
        source_url="https://example.com/new",
    )
    store.upsert(previous_trade)

    message = format_trade_alert(new_trade, store.apparent_holders("NVDA"))

    assert "NEW POLITICIAN TRADE DISCLOSURE" in message
    assert "Person: Dan Senator" in message
    assert "Disclosure delay: 16 days" in message
    assert "Carol Representative also bought NVDA" in message
