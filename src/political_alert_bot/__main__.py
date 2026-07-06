from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from political_alert_bot.config import load_sector_rules, load_sources
from political_alert_bot.disclosures import collect_trade_alerts
from political_alert_bot.feeds import fetch_source
from political_alert_bot.matcher import Alert, match_item
from political_alert_bot.state import SeenState
from political_alert_bot.telegram import format_alert, load_telegram_config, send_alert, send_text
from political_alert_bot.trades import TradeHistoryStore


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    sources = load_sources(project_root / args.sources)
    rules = load_sector_rules(project_root / args.keywords)
    state = SeenState(project_root / args.state)
    trade_history = TradeHistoryStore(project_root / args.trade_history)
    telegram_config = load_telegram_config()
    dry_run = args.dry_run or telegram_config is None

    news_alerts = collect_alerts(
        sources=sources,
        rules=rules,
        state=state,
        max_per_source=args.max_per_source,
        min_score=args.min_score,
        lookback_hours=args.lookback_hours,
        max_alerts=args.max_alerts,
    )
    trade_alerts, added_to_history = collect_trade_alerts(
        state=state,
        history=trade_history,
        lookback_hours=args.trade_lookback_hours,
        max_alerts=args.max_trade_alerts,
        include_senate=not args.no_senate,
        include_house=not args.no_house,
    )

    if not news_alerts and not trade_alerts:
        print("No new matching alerts or trade disclosures.")
        return 0

    print(f"Found {len(news_alerts)} news alert(s) and {len(trade_alerts)} trade alert(s).")
    for alert in news_alerts:
        if dry_run:
            print("\n" + "=" * 72)
            print(format_alert(alert))
            continue
        assert telegram_config is not None
        send_alert(telegram_config, alert)
        print(f"Sent Telegram alert: {alert.title}")

    for trade_alert in trade_alerts:
        if dry_run:
            print("\n" + "=" * 72)
            print(trade_alert.message)
            continue
        assert telegram_config is not None
        send_text(telegram_config, trade_alert.message)
        print(f"Sent trade alert: {trade_alert.id}")

    if not args.no_state_write:
        for alert in news_alerts:
            state.mark_seen(alert.id)
        for trade_alert in trade_alerts:
            state.mark_seen(trade_alert.id)
        state.save()
        if added_to_history > 0:
            trade_history.save()
        print(f"Updated state file: {project_root / args.state}")
        if added_to_history > 0:
            print(f"Updated trade history: {project_root / args.trade_history}")
    return 0


def collect_alerts(
    *,
    sources,
    rules,
    state: SeenState,
    max_per_source: int,
    min_score: int,
    lookback_hours: int,
    max_alerts: int,
) -> list[Alert]:
    alerts: list[Alert] = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    for source in sources:
        try:
            items = fetch_source(source, max_items=max_per_source)
        except Exception as exc:
            print(f"Warning: failed to fetch {source.name}: {exc}")
            continue
        for item in items:
            if state.has_seen(item.id):
                continue
            if item.published_at is not None and item.published_at < cutoff:
                continue
            alert = match_item(item, rules, min_score=min_score)
            if alert is not None:
                alerts.append(alert)
    alerts.sort(key=lambda alert: alert.score, reverse=True)
    return alerts[:max_alerts]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send Telegram alerts for political market events.")
    parser.add_argument("--sources", default="config/sources.yaml")
    parser.add_argument("--keywords", default="config/ticker_keywords.yaml")
    parser.add_argument("--state", default="data/seen_alerts.json")
    parser.add_argument("--trade-history", default="data/trade_history.json")
    parser.add_argument("--max-per-source", type=int, default=10)
    parser.add_argument("--max-alerts", type=int, default=10)
    parser.add_argument("--max-trade-alerts", type=int, default=10)
    parser.add_argument("--min-score", type=int, default=45)
    parser.add_argument("--lookback-hours", type=int, default=72)
    parser.add_argument("--trade-lookback-hours", type=int, default=96)
    parser.add_argument("--no-senate", action="store_true")
    parser.add_argument("--no-house", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-state-write", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
