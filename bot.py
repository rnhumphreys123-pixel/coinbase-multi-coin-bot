import schedule
import time
import subprocess


def run_trading_bot():

    print("\n========================")
    print("Running multi-coin trading check...")
    print("========================\n")

    subprocess.run([
        "venv\\Scripts\\python.exe",
        "market_data.py"
    ])


def run_daily_summary():

    print("\n========================")
    print("Sending daily summary...")
    print("========================\n")

    subprocess.run([
        "venv\\Scripts\\python.exe",
        "daily_summary.py"
    ])


def run_performance_report():

    print("\n========================")
    print("Sending performance report...")
    print("========================\n")

    subprocess.run([
        "venv\\Scripts\\python.exe",
        "performance_report.py"
    ])


def run_exit_reason_report():

    print("\n========================")
    print("Sending exit reason report...")
    print("========================\n")

    subprocess.run([
        "venv\\Scripts\\python.exe",
        "exit_reason_report.py"
    ])


schedule.every(5).minutes.do(
    run_trading_bot
)

schedule.every().day.at(
    "20:00"
).do(run_daily_summary)

schedule.every().day.at(
    "20:05"
).do(run_performance_report)

schedule.every().day.at(
    "20:10"
).do(run_exit_reason_report)


print("\n========================")
print("Multi-Coin Trading Bot Started")
print("========================")

print("\nScheduled Tasks:")
print("- Trading checks every 5 minutes")
print("- Daily summary at 8:00 PM")
print("- Performance report at 8:05 PM")
print("- Exit reason report at 8:10 PM")


while True:

    schedule.run_pending()

    time.sleep(1)