from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


BUY_ACTIONS = {"buy", "purchase", "purchased"}
SELL_ACTIONS = {"sell", "sale", "sold"}


@dataclass(frozen=True)
class PoliticalTrade:
    id: str
    person: str
    office: str
    party: str
    state: str
    action: str
    ticker: str
    company: str
    amount: str
    trade_date: str
    disclosure_date: str
    source_url: str

    @property
    def normalized_action(self) -> str:
        return self.action.strip().lower()

    @property
    def is_buy(self) -> bool:
        return self.normalized_action in BUY_ACTIONS

    @property
    def is_sell(self) -> bool:
        return self.normalized_action in SELL_ACTIONS

    @property
    def normalized_ticker(self) -> str:
        return self.ticker.strip().upper()

    @property
    def delay_days(self) -> int | None:
        trade_day = _parse_date(self.trade_date)
        disclosure_day = _parse_date(self.disclosure_date)
        if trade_day is None or disclosure_day is None:
            return None
        return (disclosure_day - trade_day).days


@dataclass(frozen=True)
class ApparentHolding:
    person: str
    office: str
    party: str
    state: str
    latest_trade_date: str
    latest_amount: str


class TradeHistoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.trades = self._load()

    def upsert(self, trade: PoliticalTrade) -> None:
        existing = {item.id: item for item in self.trades}
        existing[trade.id] = trade
        self.trades = sorted(existing.values(), key=lambda item: (item.disclosure_date, item.id))

    def apparent_holders(self, ticker: str, exclude_trade_id: str | None = None) -> list[ApparentHolding]:
        latest_by_person: dict[str, PoliticalTrade] = {}
        normalized_ticker = ticker.strip().upper()
        for trade in sorted(self.trades, key=lambda item: (_date_sort_key(item.trade_date), item.id)):
            if trade.id == exclude_trade_id or trade.normalized_ticker != normalized_ticker:
                continue
            latest_by_person[trade.person] = trade

        holders: list[ApparentHolding] = []
        for trade in latest_by_person.values():
            if not trade.is_buy:
                continue
            holders.append(
                ApparentHolding(
                    person=trade.person,
                    office=trade.office,
                    party=trade.party,
                    state=trade.state,
                    latest_trade_date=trade.trade_date,
                    latest_amount=trade.amount,
                )
            )
        return sorted(holders, key=lambda item: item.person)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"trades": [asdict(trade) for trade in self.trades]}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    def _load(self) -> list[PoliticalTrade]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        trades = payload.get("trades", [])
        if not isinstance(trades, list):
            raise ValueError(f"Invalid trades list in {self.path}")
        return [PoliticalTrade(**item) for item in trades]


def build_historical_comment(trade: PoliticalTrade, holders: list[ApparentHolding]) -> str:
    if not trade.is_buy:
        return "Historical context: this is a sale disclosure, so holding context is not applied."
    if not holders:
        return f"Historical context: no prior apparent holders of {trade.normalized_ticker} found in stored disclosures."

    names = _human_names([holder.person for holder in holders[:4]])
    more_count = max(0, len(holders) - 4)
    suffix = f" and {more_count} more" if more_count else ""
    verb = "appears" if len(holders) == 1 else "appear"
    return (
        f"Historical context: {names}{suffix} also bought {trade.normalized_ticker} "
        f"and {verb} to still be holding based on latest stored disclosures."
    )


def format_trade_alert(trade: PoliticalTrade, holders: list[ApparentHolding]) -> str:
    delay = trade.delay_days
    delay_text = f"{delay} days" if delay is not None else "unknown"
    parts = [
        "NEW POLITICIAN TRADE DISCLOSURE",
        "",
        f"Person: {trade.person}",
        f"Office: {trade.office}",
        f"Party/State: {trade.party}-{trade.state}" if trade.party and trade.state else "Party/State: unknown",
        f"Action: {trade.action.upper()}",
        f"Ticker: {trade.normalized_ticker}",
        f"Company: {trade.company}",
        f"Amount: {trade.amount}",
        f"Trade date: {trade.trade_date}",
        f"Disclosure date: {trade.disclosure_date}",
        f"Disclosure delay: {delay_text}",
        "",
        build_historical_comment(trade, holders),
    ]
    if trade.source_url:
        parts.extend(["", trade.source_url])
    return "\n".join(parts)


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_sort_key(value: str) -> date:
    return _parse_date(value) or date.min


def _human_names(names: list[str]) -> str:
    if not names:
        return "No one"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"
