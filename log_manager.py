import os
import shutil
from datetime import datetime
from notification_center import log_notification

LOG_FILES = [
    "trade_log.csv",
    "events_log.csv",
    "equity_log.csv",
    "signals_log.csv",
    "candles_log.csv"
]

ARCHIVE_FOLDER = "log_archives"


def archive_logs():

    os.makedirs(
        ARCHIVE_FOLDER,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    archived_files = []

    for log_file in LOG_FILES:

        if os.path.exists(log_file):

            archive_name = (
                f"{timestamp}_{log_file}"
            )

            archive_path = os.path.join(
                ARCHIVE_FOLDER,
                archive_name
            )

            shutil.copy2(
                log_file,
                archive_path
            )

            archived_files.append(
                archive_path
            )

    return archived_files


def clear_log_file(log_file):

    if not os.path.exists(log_file):
        return False

    with open(log_file, "r") as file:
        first_line = file.readline()

    with open(log_file, "w") as file:
        file.write(first_line)

    return True


def archive_and_clear_logs():

    archived_files = archive_logs()

    for log_file in LOG_FILES:
        clear_log_file(log_file)

    return archived_files

MAX_LOG_SIZE_MB = 5


def get_file_size_mb(file_path):

    if not os.path.exists(file_path):
        return 0

    size_bytes = os.path.getsize(file_path)

    return size_bytes / (1024 * 1024)


def auto_rotate_logs():

    rotated_files = []

    for log_file in LOG_FILES:

        file_size_mb = get_file_size_mb(log_file)

        if file_size_mb >= MAX_LOG_SIZE_MB:

            archived_files = archive_logs()

            clear_log_file(log_file)
            log_notification(
                "INFO",
                "LOG_ROTATION",
                f"Auto-rotated log: {log_file}"
            )
            rotated_files.append(log_file)

    return rotated_files