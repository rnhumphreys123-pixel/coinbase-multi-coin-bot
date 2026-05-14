import pandas as pd

from notifications import send_telegram_message

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

if "reason" not in df.columns:

    print("No reason column found.")
    exit()

sells = df[
    df["action"] == "SELL"
].copy()

if sells.empty:

    print("No completed sell trades yet.")
    exit()

sells["profit"] = (
    sells["profit"].astype(float)
)

sells["reason"] = (
    sells["reason"]
    .fillna("Unknown / Old Trade")
)

summary = sells.groupby("reason").agg(
    trades=("profit", "count"),
    total_profit=("profit", "sum"),
    average_profit=("profit", "mean"),
    wins=("profit", lambda x: (x > 0).sum()),
    losses=("profit", lambda x: (x <= 0).sum())
).reset_index()

print("\n==============================")
print("EXIT REASON REPORT")
print("==============================")

print(summary)

print("\nRecent Sell Trades:")
print(sells.tail())

message = "📉 EXIT REASON REPORT\n\n"

for _, row in summary.iterrows():

    message += (
        f"{row['reason']}\n"
        f"Trades: {row['trades']}\n"
        f"Wins: {row['wins']}\n"
        f"Losses: {row['losses']}\n"
        f"Total Profit: "
        f"${row['total_profit']:.2f}\n"
        f"Average Profit: "
        f"${row['average_profit']:.2f}\n\n"
    )

send_telegram_message(message)