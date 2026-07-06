from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from political_alert_bot.backfill_trades import normalize_trade, parse_flexible_date
from political_alert_bot.state import SeenState
from political_alert_bot.trades import TradeHistoryStore, format_trade_alert


@dataclass(frozen=True)
class TradeSource:
    name: str
    url: str
    default_office: str


@dataclass(frozen=True)
class TradeAlertMessage:
    id: str
    message: str


DEFAULT_TRADE_SOURCES = [
    TradeSource(
        name="House Stock Watcher",
        url="https://raw.githubusercontent.com/TattooedHead/house-stock-watcher-data/master/data/all_transactions.json",
        default_office="House",
    ),
    TradeSource(
        name="Senate Stock Watcher",
        url="https://raw.githubusercontent.com/timothycarambat/senate-stock-watcher-data/master/aggregate/all_transactions.json",
        default_office="Senate",
    ),
]


def collect_trade_alerts(
    *,
    state: SeenState,
    history: TradeHistoryStore,
    lookback_hours: int,
    max_alerts: int,
    include_senate: bool,
    include_house: bool,
    sources: list[TradeSource] | None = None,
) -> tuple[list[TradeAlertMessage], int]:
    selected_sources = [
        source
        for source in (sources or DEFAULT_TRADE_SOURCES)
        if (include_house and source.default_office == "House")
        or (include_senate and source.default_office == "Senate")
    ]

    cutoff = datetime.now(timezone.utc).date() - timedelta(hours=lookback_hours)
    known_ids = {trade.id for trade in history.trades}
    alerts: list[TradeAlertMessage] = []
    added_to_history = 0

    for source in selected_sources:
        try:
            records = _fetch_records(source.url)
        except Exception as exc:  # pragma: no cover - network path
            print(f"Warning: failed to fetch {source.name}: {exc}")
            continue

        for record in records:
            trade = normalize_trade(record, default_office=source.default_office)
            if trade is None:
                continue
            if trade.id in known_ids or state.has_seen(trade.id):
                continue

            disclosure_day = parse_flexible_date(trade.disclosure_date)
            trade_day = parse_flexible_date(trade.trade_date)
            relevant_day = disclosure_day or trade_day
            if relevant_day is not None and relevant_day < cutoff:
                continue

            holders = history.apparent_holders(trade.normalized_ticker, exclude_trade_id=trade.id)
            history.upsert(trade)
            known_ids.add(trade.id)
            added_to_history += 1

            if len(alerts) < max_alerts:
                alerts.append(TradeAlertMessage(id=trade.id, message=format_trade_alert(trade, holders)))

    return alerts, added_to_history


def _fetch_records(url: str) -> list[dict[str, Any]]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("transactions", "data", "results", "trades"):
            values = payload.get(key)
            if isinstance(values, list):
                return [item for item in values if isinstance(item, dict)]
    raise ValueError(f"Unsupported JSON structure for {url}")
