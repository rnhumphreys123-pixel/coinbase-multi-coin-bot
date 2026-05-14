import pandas as pd

from notifications import send_telegram_message
from config import ACTIVE_SYMBOLS

TRADE_LOG_FILE = "trade_log.csv"

try:
    df = pd.read_csv(
        TRADE_LOG_FILE,
        encoding="utf-8-sig"
    )

except FileNotFoundError:

    print("trade_log.csv not found.")
    exit()

df.columns = df.columns.str.strip()

if df.empty:

    print("No trade data found.")
    exit()

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

today = pd.Timestamp.now().date()

today_trades = df[
    df["timestamp"].dt.date == today
]

today_trades = today_trades[
    today_trades["symbol"].isin(
        ACTIVE_SYMBOLS
    )
]

sells = today_trades[
    today_trades["action"] == "SELL"
].copy()

if not sells.empty:

    sells["profit"] = (
        sells["profit"].astype(float)
    )

total_profit = (
    sells["profit"].sum()
    if not sells.empty
    else 0
)

wins = (
    (sells["profit"] > 0).sum()
    if not sells.empty
    else 0
)

losses = (
    (sells["profit"] <= 0).sum()
    if not sells.empty
    else 0
)

completed_trades = len(sells)

message = (
    "📅 DAILY BOT SUMMARY\n\n"

    f"Date: {today}\n"

    f"Active Symbols: "
    f"{', '.join(ACTIVE_SYMBOLS)}\n\n"

    f"Completed Trades: "
    f"{completed_trades}\n"

    f"Wins: {wins}\n"

    f"Losses: {losses}\n"

    f"Total Profit/Loss: "
    f"${total_profit:.2f}\n\n"
)

if not sells.empty:

    message += "By Symbol:\n"

    symbol_summary = sells.groupby(
        "symbol"
    )["profit"].sum()

    for symbol, profit in (
        symbol_summary.items()
    ):

        message += (
            f"{symbol}: "
            f"${profit:.2f}\n"
        )

else:

    message += (
        "No completed trades today."
    )

print("\n==============================")
print("DAILY BOT SUMMARY")
print("==============================")

print(message)

send_telegram_message(message)