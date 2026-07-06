# Political Alert Bot

A free Telegram alert bot for monitoring public US government announcements and mapping them to potentially affected market sectors/tickers.

This MVP is designed to run on GitHub Actions while your computer is off. It checks public RSS feeds, matches article text against a configurable keyword map, sends Telegram alerts for new matches, and stores a small `data/seen_alerts.json` state file to avoid duplicate messages.

## What It Does Now

- Monitors government/public-policy RSS feeds.
- Matches announcements to sectors and tickers using `config/ticker_keywords.yaml`.
- Scores each alert from 0-100 based on source importance and keyword strength.
- Sends Telegram messages when new relevant events appear.
- Runs locally or on GitHub Actions.

## What It Does Not Do Yet

- It does not scrape House/Senate stock trade PDFs yet.
- It does not place trades.
- It does not claim politician trades are real-time. Public trade disclosures are often delayed.

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

The workflow in `.github/workflows/monitor.yml` runs every 30 minutes and can also be started manually from GitHub's Actions tab.

## Configuration

- `config/sources.yaml`: RSS feeds to monitor.
- `config/ticker_keywords.yaml`: sector keywords and ticker mappings.
- `data/seen_alerts.json`: dedupe state committed by the workflow.

## Roadmap

1. Add House/Senate disclosure ingestion.
2. Add price movement since announcement using free price data.
3. Add politician/company/entity database.
4. Add confidence scoring for delayed disclosures.
5. Add weekly summary reports.
