from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from political_alert_bot.trades import PoliticalTrade, TradeHistoryStore


PERSON_FIELDS = ("person", "name", "representative", "senator", "member", "member_name")
OFFICE_FIELDS = ("office", "chamber", "body")
PARTY_FIELDS = ("party", "party_name")
STATE_FIELDS = ("state", "district_state")
ACTION_FIELDS = ("action", "type", "transaction_type", "transaction")
TICKER_FIELDS = ("ticker", "asset_ticker", "symbol")
COMPANY_FIELDS = ("company", "asset_description", "asset", "issuer", "issuer_name")
AMOUNT_FIELDS = ("amount", "amount_range", "range", "value")
TRADE_DATE_FIELDS = ("trade_date", "transaction_date", "date", "transactionDate")
DISCLOSURE_DATE_FIELDS = ("disclosure_date", "filing_date", "filed_date", "disclosureDate")
SOURCE_URL_FIELDS = ("source_url", "url", "link", "filing_url", "ptr_link")


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / args.output
    store = TradeHistoryStore(output_path)
    cutoff = date.today() - timedelta(days=365 * args.years)

    imported = 0
    skipped = 0
    for input_path in args.input:
        records = load_records(project_root / input_path)
        for record in records:
            trade = normalize_trade(record, default_office=args.default_office)
            if trade is None:
                skipped += 1
                continue
            trade_day = parse_flexible_date(trade.trade_date)
            disclosure_day = parse_flexible_date(trade.disclosure_date)
            relevant_day = disclosure_day or trade_day
            if relevant_day is not None and relevant_day < cutoff:
                skipped += 1
                continue
            store.upsert(trade)
            imported += 1

    if not args.dry_run:
        store.save()

    mode = "Would import" if args.dry_run else "Imported"
    print(f"{mode} {imported} trade(s); skipped {skipped}; total stored {len(store.trades)}")
    print(f"Trade history: {output_path}")
    return 0


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("trades", "transactions", "data", "results"):
                values = payload.get(key)
                if isinstance(values, list):
                    return [item for item in values if isinstance(item, dict)]
        raise ValueError(f"No record list found in {path}")
    raise ValueError(f"Unsupported input type: {path}")


def normalize_trade(record: dict[str, Any], default_office: str) -> PoliticalTrade | None:
    lowered = {str(key).strip().lower(): value for key, value in record.items()}

    person = pick(lowered, PERSON_FIELDS)
    action = normalize_action(pick(lowered, ACTION_FIELDS))
    ticker = pick(lowered, TICKER_FIELDS).upper().strip("$")
    company = pick(lowered, COMPANY_FIELDS)
    amount = pick(lowered, AMOUNT_FIELDS)
    trade_date = normalize_date(pick(lowered, TRADE_DATE_FIELDS))
    disclosure_date = normalize_date(pick(lowered, DISCLOSURE_DATE_FIELDS))
    source_url = pick(lowered, SOURCE_URL_FIELDS)

    if not person or not action or not ticker or not trade_date:
        return None

    if not disclosure_date:
        disclosure_date = trade_date

    office = pick(lowered, OFFICE_FIELDS) or default_office
    party = pick(lowered, PARTY_FIELDS)
    state = pick(lowered, STATE_FIELDS)
    trade_id = stable_trade_id(person, action, ticker, amount, trade_date, disclosure_date, source_url)

    return PoliticalTrade(
        id=trade_id,
        person=person,
        office=office,
        party=party,
        state=state,
        action=action,
        ticker=ticker,
        company=company or ticker,
        amount=amount or "unknown",
        trade_date=trade_date,
        disclosure_date=disclosure_date,
        source_url=source_url,
    )


def pick(record: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = record.get(field.lower())
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none", "null", "--", "n/a"}:
            return text
    return ""


def normalize_action(value: str) -> str:
    lowered = value.lower().strip()
    if lowered in {"p", "purchase", "purchased", "buy", "b"}:
        return "Buy"
    if lowered in {"s", "sale", "sold", "sell"}:
        return "Sell"
    if "purchase" in lowered or "buy" in lowered:
        return "Buy"
    if "sale" in lowered or "sell" in lowered or "sold" in lowered:
        return "Sell"
    return value.strip()


def normalize_date(value: str) -> str:
    parsed = parse_flexible_date(value)
    return parsed.isoformat() if parsed else ""


def parse_flexible_date(value: str) -> date | None:
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def stable_trade_id(
    person: str,
    action: str,
    ticker: str,
    amount: str,
    trade_date: str,
    disclosure_date: str,
    source_url: str,
) -> str:
    basis = "|".join([person, action, ticker, amount, trade_date, disclosure_date, source_url])
    return "trade:" + sha256(basis.encode("utf-8")).hexdigest()[:24]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill politician trade history from CSV/JSON exports.")
    parser.add_argument("--input", nargs="+", required=True, help="CSV or JSON file(s), relative to project root.")
    parser.add_argument("--output", default="data/trade_history.json")
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--default-office", default="unknown")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
