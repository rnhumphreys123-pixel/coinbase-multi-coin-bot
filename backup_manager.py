import os
import shutil
from datetime import datetime

BACKUP_FOLDER = "project_backups"

FILES_TO_BACKUP = [
    "config.py",
    "state.json",
    "bot_control.json",
    "engine_status.json",
    "telegram_control.json",
    "schedule_control.json",
    "trade_log.csv",
    "events_log.csv",
    "equity_log.csv",
    "signals_log.csv",
    "candles_log.csv"
]


def create_project_backup():

    os.makedirs(
        BACKUP_FOLDER,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = os.path.join(
        BACKUP_FOLDER,
        f"backup_{timestamp}"
    )

    os.makedirs(
        backup_path,
        exist_ok=True
    )

    copied_files = []

    for file_name in FILES_TO_BACKUP:

        if os.path.exists(file_name):

            destination = os.path.join(
                backup_path,
                file_name
            )

            shutil.copy2(
                file_name,
                destination
            )

            copied_files.append(file_name)

    return backup_path, copied_files