import time
import json
import subprocess

from datetime import datetime

HEARTBEAT_FILE = "engine_status.json"

CHECK_INTERVAL_SECONDS = 300


def update_heartbeat():

    heartbeat_data = {
        "last_heartbeat": datetime.now().isoformat()
    }

    with open(HEARTBEAT_FILE, "w") as file:
        json.dump(
            heartbeat_data,
            file,
            indent=4
        )


print("===================================")
print("COINBASE MULTI-COIN BOT STARTED")
print("===================================")

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