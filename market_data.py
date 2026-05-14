import ccxt
import pandas as pd
import os
import csv

from datetime import datetime
from dotenv import load_dotenv

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from strategy import generate_signal
from paper_trader import PaperTrader
from notifications import send_telegram_message

from config import (
    COIN_CONFIG,
    ACTIVE_SYMBOLS
)

from risk_manager import trading_allowed

# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

api_secret = os.getenv(
    "COINBASE_API_SECRET",
    ""
).replace("\\n", "\n")

exchange = ccxt.coinbase({
    "apiKey": os.getenv("COINBASE_API_KEY"),
    "secret": api_secret,
})

# --------------------------------------------------
# FILES
# --------------------------------------------------

SIGNALS_LOG_FILE = "signals_log.csv"
CANDLES_LOG_FILE = "candles_log.csv"

# --------------------------------------------------
# LOG SIGNAL
# --------------------------------------------------

def log_signal(
    symbol,
    timeframe,
    signal,
    current_price,
    rsi,
    ema_20,
    ema_50,
    ema_200,
    atr
):

    with open(
        SIGNALS_LOG_FILE,
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            datetime.now().isoformat(),
            symbol,
            timeframe,
            signal,
            round(current_price, 2),
            round(rsi, 2),
            round(ema_20, 2),
            round(ema_50, 2),
            round(ema_200, 2),
            round(atr, 2)
        ])

# --------------------------------------------------
# LOG CANDLE
# --------------------------------------------------

def log_candle(
    row,
    symbol,
    timeframe
):

    with open(
        CANDLES_LOG_FILE,
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            datetime.now().isoformat(),
            symbol,
            timeframe,
            round(row["open"], 2),
            round(row["high"], 2),
            round(row["low"], 2),
            round(row["close"], 2),
            round(row["volume"], 8),
            round(row["ema_20"], 2),
            round(row["ema_50"], 2),
            round(row["ema_200"], 2),
            round(row["rsi"], 2),
            round(row["atr"], 2),
            row["signal"]
        ])

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

for symbol in ACTIVE_SYMBOLS:

    settings = COIN_CONFIG[symbol]

    timeframe = settings["timeframe"]

    print("\n==============================")

    print(
        f"Checking {symbol} "
        f"on {timeframe}"
    )

    print("==============================")

    print("Fetching market data...")

    ohlcv = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=300
    )

    df = pd.DataFrame(
        ohlcv,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms"
    )

    # --------------------------------------------------
    # INDICATORS
    # --------------------------------------------------

    df["ema_20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema_50"] = EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    df["ema_200"] = EMAIndicator(
        close=df["close"],
        window=200
    ).ema_indicator()

    df["rsi"] = RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    )

    df["atr"] = atr.average_true_range()

    # --------------------------------------------------
    # SIGNALS
    # --------------------------------------------------

    df["signal"] = df.apply(
        lambda row: generate_signal(
            row,
            settings
        ),
        axis=1
    )

    latest = df.iloc[-1]

    signal = latest["signal"]

    current_price = latest["close"]

    atr_value = latest["atr"]

    # --------------------------------------------------
    # LOGGING
    # --------------------------------------------------

    log_signal(
        symbol,
        timeframe,
        signal,
        current_price,
        latest["rsi"],
        latest["ema_20"],
        latest["ema_50"],
        latest["ema_200"],
        latest["atr"]
    )

    log_candle(
        latest,
        symbol,
        timeframe
    )

    # --------------------------------------------------
    # PAPER TRADER
    # --------------------------------------------------

    trader = PaperTrader(symbol)

    new_trade_stop_loss = (
        current_price
        - (
            atr_value
            * settings[
                "atr_stop_multiplier"
            ]
        )
    )

    # --------------------------------------------------
    # ACTIVE POSITION
    # --------------------------------------------------

    if trader.position > 0:

        trader.update_highest_price(
            current_price
        )

        trailing_stop_price = (
            trader.highest_price
            - (
                atr_value
                * settings[
                    "atr_stop_multiplier"
                ]
            )
        )

        active_stop_loss = (
            trader.entry_price
            - (
                atr_value
                * settings[
                    "atr_stop_multiplier"
                ]
            )
        )

        active_take_profit = (
            trader.entry_price
            + (
                atr_value
                * settings[
                    "atr_take_profit_multiplier"
                ]
            )
        )

        use_trailing_stop = settings[
            "use_trailing_stop"
        ]

        sell_reason = None

        if (
            use_trailing_stop
            and current_price
            <= trailing_stop_price
        ):

            sell_reason = (
                "Trailing Stop Hit"
            )

        elif (
            current_price
            <= active_stop_loss
        ):

            sell_reason = (
                "Stop Loss Hit"
            )

        elif (
            current_price
            >= active_take_profit
        ):

            sell_reason = (
                "Take Profit Hit"
            )

        elif signal == "SELL":

            sell_reason = (
                "Signal Reversal"
            )

        if sell_reason is not None:

            message = (
                f"{sell_reason} "
                f"for {symbol} "
                f"at ${current_price:.2f}"
            )

            print(message)

            trader.log_event(
                sell_reason,
                message
            )

            trader.sell(
                current_price,
                sell_reason
            )

        else:

            message = (
                f"Holding {symbol}\n"
                f"Current Price: "
                f"${current_price:.2f}\n"
                f"Highest Price: "
                f"${trader.highest_price:.2f}\n"
                f"Trailing Stop: "
                f"${trailing_stop_price:.2f}"
            )

            print(message)

            trader.log_event(
                "HOLD",
                message
            )

    # --------------------------------------------------
    # NEW POSITION
    # --------------------------------------------------

    else:

        if signal == "BUY":

            allowed, reason = (
                trading_allowed(symbol)
            )

            if allowed:

                trader.buy(
                    current_price,
                    new_trade_stop_loss,
                    settings[
                        "risk_per_trade"
                    ]
                )

            else:

                message = (
                    f"Trade blocked "
                    f"for {symbol}: "
                    f"{reason}"
                )

                print(message)

                trader.log_event(
                    "RISK_BLOCK",
                    message
                )

                send_telegram_message(
                    message
                )

        else:

            message = (
                f"No trade for "
                f"{symbol}."
            )

            print(message)

            trader.log_event(
                "NO_TRADE",
                message
            )

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    trader.status(
        current_price,
        atr_value,
        settings[
            "atr_stop_multiplier"
        ]
    )

    # --------------------------------------------------
    # DEBUG OUTPUT
    # --------------------------------------------------

    print(df.tail())

    print("\nLatest Signal:")

    print(f"{symbol}: {signal}")

    print(
        f"Timeframe: "
        f"{timeframe}"
    )

    print(
        f"Close: "
        f"{current_price}"
    )

    print(
        f"RSI: "
        f"{latest['rsi']:.2f}"
    )

    print(
        f"EMA 20: "
        f"{latest['ema_20']:.2f}"
    )

    print(
        f"EMA 50: "
        f"{latest['ema_50']:.2f}"
    )

    print(
        f"EMA 200: "
        f"{latest['ema_200']:.2f}"
    )

    print(
        f"ATR: "
        f"{latest['atr']:.2f}"
    )