# Coinbase Bot Runbook

## Start the System

1. Start the engine:
```powershell
python bot.py

## Current Project Status

- Mode: Paper trading only
- Live orders: Locked
- Active coins: BTC/USD and SOL/USD
- Engine: Runs through `bot.py`
- Dashboard: Runs through `dashboard.py`
- Strategy: EMA 20 / EMA 50 + RSI + EMA 200 filter
- Risk: Per-coin allocation, drawdown limits, exposure limits
- Alerts: Telegram controlled from dashboard
- Backups: Available from dashboard Config tab

## Current Launch Files

- `start_bot.bat` starts the engine
- `start_dashboard.bat` starts the dashboard