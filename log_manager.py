import os
import shutil
from datetime import datetime

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