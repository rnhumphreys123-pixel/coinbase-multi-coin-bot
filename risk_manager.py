import csv
import json
from datetime import datetime

from config import (
    RISK_SETTINGS,
    COIN_CONFIG,
    ACTIVE_SYMBOLS,
    PORTFOLIO_SETTINGS
)

TRADE_LOG_FILE = "trade_log.csv"
STATE_FILE = "state.json"


def get_today_profit(symbol=None):

    total_profit = 0
    today = datetime.now().date()

    try:
        with open(TRADE_LOG_FILE, "r") as file:
            reader = csv.DictReader(file)

            for row in reader:

                if row["action"] != "SELL":
                    continue

                if symbol is not None and row["symbol"] != symbol:
                    continue

                trade_date = datetime.fromisoformat(
                    row["timestamp"]
                ).date()

                if trade_date == today:
                    total_profit += float(row["profit"])

    except FileNotFoundError:
        return 0

    return total_profit


def load_state():

    try:
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return {}


def get_total_exposure():

    state = load_state()

    total_position_value = 0
    total_portfolio_value = 0

    for symbol in ACTIVE_SYMBOLS:

        coin_state = state.get(symbol, {})

        balance = coin_state.get("balance", 0)
        position = coin_state.get("position", 0)
        entry_price = coin_state.get("entry_price", 0)

        position_value = position * entry_price

        total_position_value += position_value
        total_portfolio_value += balance + position_value

    if total_portfolio_value == 0:
        return 0

    return total_position_value / total_portfolio_value


def get_open_position_count():

    state = load_state()

    count = 0

    for symbol in ACTIVE_SYMBOLS:

        coin_state = state.get(symbol, {})

        if coin_state.get("position", 0) > 0:
            count += 1

    return count


def get_coin_drawdown(symbol):

    state = load_state()

    coin_state = state.get(symbol, {})

    balance = coin_state.get("balance", 0)
    position = coin_state.get("position", 0)
    entry_price = coin_state.get("entry_price", 0)

    current_value = balance + (position * entry_price)

    starting_balance = (
        PORTFOLIO_SETTINGS["starting_balance"]
        * COIN_CONFIG[symbol]["allocation"]
    )

    if starting_balance == 0:
        return 0

    return (current_value - starting_balance) / starting_balance


def get_portfolio_drawdown():

    state = load_state()

    total_current_value = 0

    for symbol in ACTIVE_SYMBOLS:

        coin_state = state.get(symbol, {})

        balance = coin_state.get("balance", 0)
        position = coin_state.get("position", 0)
        entry_price = coin_state.get("entry_price", 0)

        total_current_value += balance + (position * entry_price)

    starting_balance = PORTFOLIO_SETTINGS["starting_balance"]

    if starting_balance == 0:
        return 0

    return (total_current_value - starting_balance) / starting_balance


def trading_allowed(symbol):

    today_profit = get_today_profit()

    if today_profit <= RISK_SETTINGS["daily_loss_limit"]:
        return False, "Daily loss limit reached"

    total_exposure = get_total_exposure()

    if total_exposure >= RISK_SETTINGS["max_total_exposure"]:
        return False, "Max total exposure reached"

    open_positions = get_open_position_count()

    if open_positions >= RISK_SETTINGS["max_open_positions"]:
        return False, "Max open positions reached"

    portfolio_drawdown = get_portfolio_drawdown()

    if portfolio_drawdown <= RISK_SETTINGS["portfolio_drawdown_limit"]:
        return False, "Portfolio drawdown limit reached"

    coin_drawdown = get_coin_drawdown(symbol)

    if coin_drawdown <= COIN_CONFIG[symbol]["coin_drawdown_limit"]:
        return False, f"{symbol} drawdown limit reached"

    return True, "Trading allowed"