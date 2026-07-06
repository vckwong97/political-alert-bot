# Political Alert Bot

A free Telegram alert bot for monitoring public US politician/government trading disclosures and market-moving public announcements.

This MVP is designed to run on GitHub Actions while your computer is off. It stores seen alerts and trade history locally in JSON files committed by the workflow, so future alerts can include historical context such as: "X and Y also bought this stock and appear to still be holding."

## What It Does Now

- Monitors government/public-policy RSS feeds.
- Provides a trade-history storage layer for politician buy/sell disclosures.
- Formats politician trade alerts with person, action, ticker, amount, trade date, disclosure date, and historical context.
- Matches announcements to sectors and tickers using `config/ticker_keywords.yaml`.
- Scores each alert from 0-100 based on source importance and keyword strength.
- Sends Telegram messages when new relevant events appear.
- Runs locally or on GitHub Actions.

## What It Does Not Do Yet

- It does not scrape House/Senate stock trade PDFs yet. The storage and message format are ready for that parser.
- It does not place trades.
- It does not claim politician trades are real-time. Public trade disclosures are often delayed.

## Trade Alert Format

When the House/Senate parser is added, politician trade alerts will look like this:

```text
NEW POLITICIAN TRADE DISCLOSURE

Person: Dan Senator
Office: Senate
Party/State: I-VT
Action: BUY
Ticker: NVDA
Company: NVIDIA Corp.
Amount: $50,001-$100,000
Trade date: 2026-06-20
Disclosure date: 2026-07-06
Disclosure delay: 16 days

Historical context: Carol Representative also bought NVDA and appears to still be holding based on latest stored disclosures.

https://example.com/source-filing
```

Holding status is based only on latest stored disclosures. If someone later discloses a sale for the same ticker, they stop showing as an apparent holder.

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
```

Run a dry run without Telegram:

```bash
.venv/bin/python -m political_alert_bot --dry-run --no-state-write --max-per-source 3
```

Run with Telegram secrets exported:

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="123456789"
.venv/bin/python -m political_alert_bot --max-per-source 5
```

By default, the bot only considers feed items published in the last 72 hours and sends at most 10 alerts per run. You can tune this with `--lookback-hours` and `--max-alerts`.

## Backfill Two Years Of Trades

For useful "who else appears to hold this stock" comments, seed the trade history before relying on live alerts.

Current seeded baseline:

```text
House trades stored: 4,266
Senate trades stored: 0
```

The House baseline was imported from a public House stock watcher mirror. The public Senate mirror checked during setup only covered older transactions through 2019, so it did not seed the current 2-year window.

Put a CSV or JSON export in `data/imports/`, then run:

```bash
.venv/bin/python -m political_alert_bot.backfill_trades --input data/imports/trades.csv --years 2 --default-office House
```

Dry-run first:

```bash
.venv/bin/python -m political_alert_bot.backfill_trades --input data/imports/trades.csv --years 2 --dry-run
```

The importer accepts common columns such as:

```text
person/name/representative/senator/member
action/type/transaction_type
ticker/asset_ticker/symbol
company/asset_description/issuer
amount/amount_range/value
trade_date/transaction_date/date
disclosure_date/filing_date/filed_date
source_url/url/link/filing_url
party/state/office
```

It writes normalized records into `data/trade_history.json`. The live alert formatter can then add historical context like:

```text
Historical context: Alice Member and Bob Senator also bought NVDA and appear to still be holding based on latest stored disclosures.
```

## Telegram Setup

1. In Telegram, message `@BotFather`.
2. Create a bot with `/newbot`.
3. Copy the bot token into a GitHub secret named `TELEGRAM_BOT_TOKEN`.
4. Send one message to your bot from your Telegram account.
5. Open this URL in a browser, replacing the token:

```text
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

6. Find your numeric chat id and save it as GitHub secret `TELEGRAM_CHAT_ID`.

## GitHub Actions Setup

Add these repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The workflow in `.github/workflows/monitor.yml` runs every 30 minutes and can also be started manually from GitHub's Actions tab. After each run, it commits changes to `data/seen_alerts.json` and `data/trade_history.json`, so the next run starts with the latest known alert/trade state.

## Configuration

- `config/sources.yaml`: RSS feeds to monitor.
- `config/ticker_keywords.yaml`: sector keywords and ticker mappings.
- `data/seen_alerts.json`: dedupe state committed by the workflow.
- `data/trade_history.json`: stored politician trades used for historical comments.

## Roadmap

1. Add House/Senate disclosure ingestion.
2. Add politician/company/entity database.
3. Add confidence scoring for delayed disclosures.
4. Add weekly summary reports.
