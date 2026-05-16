import os

LOG_FILES = [
    "trade_log.csv",
    "events_log.csv",
    "equity_log.csv",
    "signals_log.csv",
    "candles_log.csv"
]


def get_file_size_mb(file_path):

    if not os.path.exists(file_path):
        return 0

    size_bytes = os.path.getsize(file_path)

    return size_bytes / (1024 * 1024)


def get_log_health():

    rows = []

    for log_file in LOG_FILES:

        size_mb = get_file_size_mb(log_file)

        status = "OK"

        if size_mb >= 5:
            status = "ROTATION NEEDED"

        rows.append({
            "File": log_file,
            "Size MB": round(size_mb, 3),
            "Status": status
        })

    return rows
