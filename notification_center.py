import csv
from datetime import datetime

NOTIFICATION_FILE = "notification_center.csv"


def log_notification(level, category, message):

    with open(
        NOTIFICATION_FILE,
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            datetime.now().isoformat(),
            level,
            category,
            message
        ])