import time
import json
import subprocess
import os

from datetime import datetime, date

HEARTBEAT_FILE = "engine_status.json"
SCHEDULE_FILE = "schedule_control.json"


def load_engine_status():

    try:
        with open(HEARTBEAT_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return {}


def save_engine_status(status):

    with open(HEARTBEAT_FILE, "w") as file:
        json.dump(status, file, indent=4)


def update_heartbeat():

    status = load_engine_status()

    status["last_heartbeat"] = datetime.now().isoformat()
    status["engine_pid"] = os.getpid()

    save_engine_status(status)


def load_schedule():

    try:
        with open(SCHEDULE_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return {
            "trading_check_minutes": 5,
            "daily_summary_enabled": True,
            "daily_summary_time": "20:00",
            "performance_report_enabled": True,
            "performance_report_time": "20:05",
            "exit_reason_report_enabled": True,
            "exit_reason_report_time": "20:10"
        }


def run_script(script_name):

    subprocess.run(
        ["venv\\Scripts\\python.exe", script_name]
    )


last_daily_summary_date = None
last_performance_report_date = None
last_exit_reason_report_date = None


print("===================================")
print("COINBASE MULTI-COIN BOT STARTED")
print("===================================")

update_heartbeat()

while True:

    try:

        schedule_settings = load_schedule()

        check_minutes = schedule_settings.get(
            "trading_check_minutes",
            5
        )

        print("\n-----------------------------------")
        print(f"Bot cycle started: {datetime.now()}")
        print("-----------------------------------")

        update_heartbeat()

        run_script("market_data.py")

        update_heartbeat()

        now = datetime.now()
        today = date.today()
        current_time = now.strftime("%H:%M")

        if (
            schedule_settings.get("daily_summary_enabled", True)
            and current_time >= schedule_settings.get("daily_summary_time", "20:00")
            and last_daily_summary_date != today
        ):

            print("Sending daily summary...")
            run_script("daily_summary.py")
            last_daily_summary_date = today

        if (
            schedule_settings.get("performance_report_enabled", True)
            and current_time >= schedule_settings.get("performance_report_time", "20:05")
            and last_performance_report_date != today
        ):

            print("Sending performance report...")
            run_script("performance_report.py")
            last_performance_report_date = today

        if (
            schedule_settings.get("exit_reason_report_enabled", True)
            and current_time >= schedule_settings.get("exit_reason_report_time", "20:10")
            and last_exit_reason_report_date != today
        ):

            print("Sending exit reason report...")
            run_script("exit_reason_report.py")
            last_exit_reason_report_date = today

        sleep_seconds = check_minutes * 60

        print(f"\nSleeping for {sleep_seconds} seconds...")

        time.sleep(sleep_seconds)

    except Exception as error:

        print(f"\nBOT ERROR: {error}")

        time.sleep(30)