import json
import csv
from datetime import datetime

from notifications import send_telegram_message
from config import COIN_CONFIG, PORTFOLIO_SETTINGS

STATE_FILE = "state.json"
TRADE_LOG_FILE = "trade_log.csv"
EVENT_LOG_FILE = "events_log.csv"
EQUITY_LOG_FILE = "equity_log.csv"


class PaperTrader:

    def __init__(self, symbol):

        self.symbol = symbol

        total_starting_balance = PORTFOLIO_SETTINGS[
            "starting_balance"
        ]

        allocation = COIN_CONFIG[symbol][
            "allocation"
        ]

        self.starting_balance = (
            total_starting_balance * allocation
        )

        self.load_state()

    def load_state(self):

        try:
            with open(STATE_FILE, "r") as file:
                state = json.load(file)

        except FileNotFoundError:
            state = {}

        if self.symbol not in state:

            state[self.symbol] = {
                "balance": self.starting_balance,
                "position": 0,
                "entry_price": 0,
                "highest_price": 0,
                "current_price": 0,
                "trailing_stop_price": 0
            }

            with open(STATE_FILE, "w") as file:
                json.dump(state, file, indent=4)

        self.balance = state[self.symbol].get(
            "balance",
            self.starting_balance
        )

        self.position = state[self.symbol].get(
            "position",
            0
        )

        self.entry_price = state[self.symbol].get(
            "entry_price",
            0
        )

        self.highest_price = state[self.symbol].get(
            "highest_price",
            self.entry_price
        )

        self.current_price = state[self.symbol].get(
            "current_price",
            0
        )

        self.trailing_stop_price = state[self.symbol].get(
            "trailing_stop_price",
            0
        )

        if self.position > 0 and self.highest_price == 0:

            self.highest_price = self.entry_price
            self.save_state()

    def save_state(self):

        try:
            with open(STATE_FILE, "r") as file:
                state = json.load(file)

        except FileNotFoundError:
            state = {}

        state[self.symbol] = {
            "balance": self.balance,
            "position": self.position,
            "entry_price": self.entry_price,
            "highest_price": self.highest_price,
            "current_price": self.current_price,
            "trailing_stop_price": self.trailing_stop_price
        }

        with open(STATE_FILE, "w") as file:
            json.dump(state, file, indent=4)

    def update_market_info(
        self,
        current_price,
        trailing_stop_price=0
    ):

        self.current_price = current_price
        self.trailing_stop_price = trailing_stop_price

        self.save_state()

    def update_highest_price(self, current_price):

        if (
            self.position > 0
            and current_price > self.highest_price
        ):

            self.highest_price = current_price
            self.save_state()

    def log_trade(
        self,
        action,
        price,
        profit=0,
        reason=""
    ):

        with open(
            TRADE_LOG_FILE,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                datetime.now().isoformat(),
                self.symbol,
                action,
                round(price, 2),
                round(self.balance, 2),
                round(self.position, 8),
                round(profit, 2),
                reason
            ])

    def log_event(self, event, message):

        with open(
            EVENT_LOG_FILE,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                datetime.now().isoformat(),
                self.symbol,
                event,
                message
            ])

    def log_equity(self, current_price):

        position_value = (
            self.position * current_price
        )

        total_value = (
            self.balance + position_value
        )

        with open(
            EQUITY_LOG_FILE,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                datetime.now().isoformat(),
                self.symbol,
                round(total_value, 2),
                round(self.balance, 2),
                round(position_value, 2),
                round(current_price, 2)
            ])

    def buy(
        self,
        price,
        stop_loss_price=None,
        risk_per_trade=0.01
    ):

        if self.position == 0:

            if stop_loss_price is None:

                amount_to_spend = self.balance

            else:

                risk_amount = (
                    self.balance
                    * risk_per_trade
                )

                stop_distance = (
                    price - stop_loss_price
                )

                if stop_distance <= 0:

                    print(
                        "Invalid stop loss distance. "
                        "No trade taken."
                    )

                    return

                position_size = (
                    risk_amount
                    / stop_distance
                )

                amount_to_spend = (
                    position_size * price
                )

                if amount_to_spend > self.balance:

                    amount_to_spend = self.balance

            self.position = (
                amount_to_spend / price
            )

            self.entry_price = price
            self.highest_price = price
            self.current_price = price

            self.balance -= amount_to_spend

            self.save_state()

            self.log_trade(
                "BUY",
                price
            )

            print(
                f"BUY {self.symbol} "
                f"at ${price:.2f}"
            )

            print(
                f"Amount Spent: "
                f"${amount_to_spend:.2f}"
            )

            print(
                f"Risk Per Trade: "
                f"{risk_per_trade * 100:.2f}%"
            )

            send_telegram_message(
                f"🟢 BUY {self.symbol}\n"
                f"Price: ${price:.2f}\n"
                f"Amount: ${amount_to_spend:.2f}\n"
                f"Risk: {risk_per_trade * 100:.2f}%"
            )

        else:

            print(
                f"Already in "
                f"{self.symbol} position."
            )

    def sell(
        self,
        price,
        reason="Unknown"
    ):

        if self.position > 0:

            position_value = (
                self.position * price
            )

            self.balance += position_value

            profit = (
                position_value
                - (
                    self.position
                    * self.entry_price
                )
            )

            print(
                f"SELL {self.symbol} "
                f"at ${price:.2f}"
            )

            print(f"Reason: {reason}")

            print(
                f"Profit: "
                f"${profit:.2f}"
            )

            self.log_trade(
                "SELL",
                price,
                profit,
                reason
            )

            send_telegram_message(
                f"🔴 SELL {self.symbol}\n"
                f"Price: ${price:.2f}\n"
                f"Profit: ${profit:.2f}\n"
                f"Reason: {reason}"
            )

            self.position = 0
            self.entry_price = 0
            self.highest_price = 0
            self.current_price = price
            self.trailing_stop_price = 0

            self.save_state()

        else:

            print(
                f"No active "
                f"{self.symbol} position."
            )

    def status(
        self,
        current_price,
        atr_value=None,
        atr_multiplier=2
    ):

        position_value = (
            self.position * current_price
        )

        total_value = (
            self.balance + position_value
        )

        trailing_stop = None

        if (
            self.position > 0
            and atr_value is not None
        ):

            trailing_stop = (
                self.highest_price
                - (
                    atr_value
                    * atr_multiplier
                )
            )

            self.trailing_stop_price = trailing_stop

        self.current_price = current_price

        self.save_state()

        self.log_equity(current_price)

        print("\n--- Portfolio Status ---")

        print(f"Symbol: {self.symbol}")

        print(
            f"Total Portfolio Value: "
            f"${total_value:.2f}"
        )

        print(
            f"Cash Balance: "
            f"${self.balance:.2f}"
        )

        print(
            f"Position Value: "
            f"${position_value:.2f}"
        )

        print(
            f"Position Size: "
            f"{self.position:.6f}"
        )

        print(
            f"Entry Price: "
            f"${self.entry_price:.2f}"
        )

        print(
            f"Highest Price Since Entry: "
            f"${self.highest_price:.2f}"
        )

        if trailing_stop is not None:

            print(
                f"Trailing Stop Price: "
                f"${trailing_stop:.2f}"
            )