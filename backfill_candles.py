import ccxt
import pandas as pd
import csv
from datetime import datetime

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from strategy import generate_signal
from config import COIN_CONFIG, ACTIVE_SYMBOLS

CANDLES_LOG_FILE = "candles_log.csv"

exchange = ccxt.coinbase()


with open(CANDLES_LOG_FILE, "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "timestamp",
        "symbol",
        "timeframe",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ema_20",
        "ema_50",
        "ema_200",
        "rsi",
        "atr",
        "signal"
    ])

    for symbol in ACTIVE_SYMBOLS:

        settings = COIN_CONFIG[symbol]
        timeframe = settings["timeframe"]

        print(f"Backfilling {symbol} on {timeframe}...")

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

        df["signal"] = df.apply(
            lambda row: generate_signal(row, settings),
            axis=1
        )

        df = df.dropna()

        for _, row in df.iterrows():

            writer.writerow([
                row["timestamp"].isoformat(),
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

print("Candle history backfill complete.")