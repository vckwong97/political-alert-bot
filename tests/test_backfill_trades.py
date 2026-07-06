import csv
import json
from pathlib import Path

from political_alert_bot.backfill_trades import load_records, normalize_trade


def test_load_records_reads_csv(tmp_path: Path) -> None:
    path = tmp_path / "trades.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["person", "ticker"])
        writer.writeheader()
        writer.writerow({"person": "Alice Member", "ticker": "NVDA"})

    assert load_records(path) == [{"person": "Alice Member", "ticker": "NVDA"}]


def test_load_records_reads_json_wrapped_transactions(tmp_path: Path) -> None:
    path = tmp_path / "trades.json"
    path.write_text(json.dumps({"transactions": [{"person": "Alice Member"}]}), encoding="utf-8")

    assert load_records(path) == [{"person": "Alice Member"}]


def test_normalize_trade_accepts_common_export_columns() -> None:
    trade = normalize_trade(
        {
            "Representative": "Alice Member",
            "Transaction_Type": "Purchase",
            "Ticker": "nvda",
            "Asset_Description": "NVIDIA Corp.",
            "Amount": "$15,001-$50,000",
            "Transaction_Date": "06/20/2026",
            "Filing_Date": "2026-07-06",
            "Link": "https://example.com/filing",
            "Party": "D",
            "State": "CA",
        },
        default_office="House",
    )

    assert trade is not None
    assert trade.person == "Alice Member"
    assert trade.office == "House"
    assert trade.action == "Buy"
    assert trade.ticker == "NVDA"
    assert trade.trade_date == "2026-06-20"
    assert trade.disclosure_date == "2026-07-06"
