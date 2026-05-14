import ccxt
import pandas as pd

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from strategy import generate_signal
from config import COIN_CONFIG

exchange = ccxt.coinbase()

starting_balance = 1000
fee_rate = 0.0025

for symbol, settings in COIN_CONFIG.items():


    if settings["allocation"] <= 0:
        print(f"\nSkipping {symbol} because allocation is 0%.")
        continue

    timeframe = settings["timeframe"]

    print("\n==============================")
    print(f"Backtesting {symbol} on {timeframe}")
    print("==============================")

    print("Fetching historical data...")

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
        lambda row: generate_signal(
            row,
            settings
        ),
        axis=1
    )

    balance = (
        starting_balance
        * settings["allocation"]
    )

    position = 0
    entry_price = 0
    highest_price = 0

    trades = []
    equity_curve = []

    for _, row in df.iterrows():

        price = row["close"]
        signal = row["signal"]
        atr_value = row["atr"]

        current_value = (
            balance
            if position == 0
            else balance + (position * price)
        )

        equity_curve.append(current_value)

        if position == 0 and signal == "BUY":

            stop_loss_price = (
                price
                - (
                    atr_value
                    * settings[
                        "atr_stop_multiplier"
                    ]
                )
            )

            risk_per_trade = settings[
                "risk_per_trade"
            ]

            risk_amount = (
                balance * risk_per_trade
            )

            stop_distance = (
                price - stop_loss_price
            )

            if stop_distance <= 0:
                continue

            position_size = (
                risk_amount / stop_distance
            )

            amount_to_spend = (
                position_size * price
            )

            if amount_to_spend > balance:
                amount_to_spend = balance

            buy_amount_after_fee = (
                amount_to_spend
                * (1 - fee_rate)
            )

            position = (
                buy_amount_after_fee / price
            )

            entry_price = price
            highest_price = price

            balance -= amount_to_spend

            trades.append((
                "BUY",
                row["timestamp"],
                price,
                0,
                ""
            ))

        elif position > 0:

            if price > highest_price:
                highest_price = price

            trailing_stop = (
                highest_price
                - (
                    atr_value
                    * settings[
                        "atr_stop_multiplier"
                    ]
                )
            )

            active_stop_loss = (
                entry_price
                - (
                    atr_value
                    * settings[
                        "atr_stop_multiplier"
                    ]
                )
            )

            active_take_profit = (
                entry_price
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
                and price <= trailing_stop
            ):

                sell_reason = "Trailing Stop Hit"

            elif price <= active_stop_loss:

                sell_reason = "Stop Loss Hit"

            elif price >= active_take_profit:

                sell_reason = "Take Profit Hit"

            elif signal == "SELL":

                sell_reason = "Signal Reversal"

            if sell_reason is not None:

                gross_position_value = (
                    position * price
                )

                sell_value_after_fee = (
                    gross_position_value
                    * (1 - fee_rate)
                )

                cost_basis = (
                    position * entry_price
                )

                profit = (
                    sell_value_after_fee
                    - cost_basis
                )

                balance += sell_value_after_fee

                trades.append((
                    "SELL",
                    row["timestamp"],
                    price,
                    profit,
                    sell_reason
                ))

                position = 0
                entry_price = 0
                highest_price = 0

    final_value = (
        balance + (
            position
            * df.iloc[-1]["close"]
        )
        if position > 0
        else balance
    )

    starting_coin_balance = (
        starting_balance
        * settings["allocation"]
    )

    profit = (
        final_value
        - starting_coin_balance
    )

    sell_trades = [
        trade for trade in trades
        if trade[0] == "SELL"
    ]

    winning_trades = [
        trade for trade in sell_trades
        if trade[3] > 0
    ]

    losing_trades = [
        trade for trade in sell_trades
        if trade[3] <= 0
    ]

    win_rate = (
        len(winning_trades)
        / len(sell_trades)
        * 100
        if sell_trades
        else 0
    )

    equity_series = pd.Series(
        equity_curve
    )

    rolling_peak = (
        equity_series.cummax()
    )

    drawdown = (
        (equity_series - rolling_peak)
        / rolling_peak
    )

    max_drawdown = (
        drawdown.min() * 100
    )

    print("\n--- EMA 200 Backtest Results ---")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Allocation: {settings['allocation'] * 100:.0f}%")
    print(f"Starting Balance: ${starting_coin_balance:.2f}")
    print(f"Final Value: ${final_value:.2f}")
    print(f"Profit/Loss: ${profit:.2f}")

    if starting_coin_balance > 0:
        print(
            f"Return: "
            f"{(profit / starting_coin_balance) * 100:.2f}%"
        )
    else:
        print("Return: N/A")

    print(f"Completed Trades: {len(sell_trades)}")
    print(f"Winning Trades: {len(winning_trades)}")
    print(f"Losing Trades: {len(losing_trades)}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Risk Per Trade: {settings['risk_per_trade'] * 100:.2f}%")
    print(f"Trailing Stop Enabled: {settings['use_trailing_stop']}")
    print(f"EMA 200 Filter Enabled: {settings['use_ema200_filter']}")

    print("\nRecent Trades:")
    for trade in trades[-10:]:
        print(trade)