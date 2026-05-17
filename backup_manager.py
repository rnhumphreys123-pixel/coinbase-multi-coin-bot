import os
import shutil
from datetime import datetime
from notification_center import log_notification

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

    log_notification(
        "INFO",
        "BACKUP",
        f"Project backup created: {backup_path}"
    )

    return backup_path, copied_files

def list_project_backups():

    if not os.path.exists(BACKUP_FOLDER):
        return []

    backups = []

    for folder_name in os.listdir(BACKUP_FOLDER):

        folder_path = os.path.join(
            BACKUP_FOLDER,
            folder_name
        )

        if os.path.isdir(folder_path):

            backups.append({
                "name": folder_name,
                "path": folder_path
            })

    backups = sorted(
        backups,
        key=lambda item: item["name"],
        reverse=True
    )

    return backups


def restore_backup(backup_path):

    restored_files = []

    for file_name in FILES_TO_BACKUP:

        source = os.path.join(
            backup_path,
            file_name
        )

        if os.path.exists(source):

            shutil.copy2(
                source,
                file_name
            )

            restored_files.append(file_name)

    log_notification(
        "WARNING",
        "BACKUP",
        f"Backup restored from: {backup_path}"
    )

    return restored_files
