import os
import json
import requests

from dotenv import load_dotenv
from config import TELEGRAM_SETTINGS

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_CONTROL_FILE = "telegram_control.json"


def load_telegram_settings():
    try:
        with open(TELEGRAM_CONTROL_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return TELEGRAM_SETTINGS


def telegram_enabled(alert_type):
    settings = load_telegram_settings()

    return settings.get(
        alert_type,
        TELEGRAM_SETTINGS.get(alert_type, True)
    )


def send_telegram_message(message, alert_type="general"):
    if not telegram_enabled(alert_type):
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)

    print(response.status_code)
    print(response.text)