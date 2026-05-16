import pandas as pd

from notifications import send_telegram_message
from config import PORTFOLIO_SETTINGS, ACTIVE_SYMBOLS

EQUITY_LOG_FILE = "equity_log.csv"

try:
    df = pd.read_csv(EQUITY_LOG_FILE, encoding="utf-8-sig")
except FileNotFoundError:
    print("equity_log.csv not found.")
    exit()

df.columns = df.columns.str.strip()

if df.empty:
    print("No equity data found.")
    exit()

df["timestamp"] = pd.to_datetime(df["timestamp"])

df = df[df["symbol"].isin(ACTIVE_SYMBOLS)]

latest_rows = (
    df.sort_values("timestamp")
    .groupby("symbol")
    .tail(1)
)

total_current_value = latest_rows["total_value"].sum()
starting_value = PORTFOLIO_SETTINGS["starting_balance"]

profit = total_current_value - starting_value
return_pct = (profit / starting_value) * 100

print("\n==============================")
print("SHARED PORTFOLIO REPORT")
print("==============================")

print(f"Starting Portfolio Value: ${starting_value:.2f}")
print(f"Current Portfolio Value: ${total_current_value:.2f}")
print(f"Profit/Loss: ${profit:.2f}")
print(f"Return: {return_pct:.2f}%")

print("\nBy Symbol:")

message = (
    "📊 SHARED PORTFOLIO REPORT\n\n"
    f"Starting Value: ${starting_value:.2f}\n"
    f"Current Value: ${total_current_value:.2f}\n"
    f"Profit/Loss: ${profit:.2f}\n"
    f"Return: {return_pct:.2f}%\n\n"
    "By Symbol:\n"
)

for _, row in latest_rows.iterrows():
    line = (
        f"{row['symbol']}: "
        f"${row['total_value']:.2f} "
        f"(Cash: ${row['cash_balance']:.2f}, "
        f"Position: ${row['position_value']:.2f})"
    )

    print(line)
    message += line + "\n"

send_telegram_message(
    message,
    "send_performance_report"
)