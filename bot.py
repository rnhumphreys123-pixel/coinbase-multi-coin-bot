import time
import json
import subprocess
import os

from datetime import datetime

HEARTBEAT_FILE = "engine_status.json"

CHECK_INTERVAL_SECONDS = 300


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


print("===================================")
print("COINBASE MULTI-COIN BOT STARTED")
print("===================================")

update_heartbeat()

while True:

    try:

        print("\n-----------------------------------")
        print(
            f"Bot cycle started: "
            f"{datetime.now()}"
        )
        print("-----------------------------------")

        update_heartbeat()

        subprocess.run(
            ["venv\\Scripts\\python.exe", "market_data.py"]
        )

        update_heartbeat()

        print(
            f"\nSleeping for "
            f"{CHECK_INTERVAL_SECONDS} seconds..."
        )

        time.sleep(
            CHECK_INTERVAL_SECONDS
        )

    except Exception as error:

        print(
            f"\nBOT ERROR: {error}"
        )

        time.sleep(30)