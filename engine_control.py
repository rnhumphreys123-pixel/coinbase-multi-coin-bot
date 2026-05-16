import json
import subprocess
from datetime import datetime
import pandas as pd

ENGINE_STATUS_FILE = "engine_status.json"


def load_engine_status():
    try:
        with open(ENGINE_STATUS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "last_heartbeat": None,
            "engine_pid": None
        }


def save_engine_status(status):
    with open(ENGINE_STATUS_FILE, "w") as file:
        json.dump(status, file, indent=4)


def heartbeat_is_fresh(seconds=420):
    status = load_engine_status()

    last_heartbeat = status.get("last_heartbeat")

    if not last_heartbeat:
        return False

    heartbeat_time = pd.to_datetime(
        last_heartbeat,
        errors="coerce"
    )

    if pd.isna(heartbeat_time):
        return False

    age_seconds = (
        pd.Timestamp.now()
        - heartbeat_time
    ).total_seconds()

    return age_seconds <= seconds


def start_engine():
    status = load_engine_status()

    existing_pid = status.get("engine_pid")

    if existing_pid and heartbeat_is_fresh():
        return False, f"Engine already appears online. PID: {existing_pid}"

    process = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "bot.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    status["engine_pid"] = process.pid
    status["last_started"] = datetime.now().isoformat()

    save_engine_status(status)

    return True, f"Engine started. PID: {process.pid}"


def stop_engine():
    status = load_engine_status()

    pid = status.get("engine_pid")

    if not pid:
        return False, "No engine PID found."

    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True
        )

        status["engine_pid"] = None
        status["last_heartbeat"] = None
        status["last_stopped"] = datetime.now().isoformat()

        save_engine_status(status)

        return True, "Engine stopped."

    except Exception as error:
        return False, f"Error stopping engine: {error}"


def restart_engine():
    stop_engine()
    return start_engine()