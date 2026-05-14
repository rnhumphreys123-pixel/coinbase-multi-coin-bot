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

risk_levels = [0.01, 0.02, 0.05]
trailing_options = [True, False]

results = []

for symbol, settings in COIN_CONFIG.items():

    if settings["allocation"] <= 0:
        print(f"\nSkipping {symbol} because allocation is 0%.")
        continue

    timeframe = settings["timeframe"]

    print("\n==============================")
    print(f"Optimizing {symbol} on {timeframe}")
    print("==============================")

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

    for risk_per_trade in risk_levels:

        for use_trailing_stop in trailing_options:

            test_settings = settings.copy()

            test_settings[
                "risk_per_trade"
            ] = risk_per_trade

            test_settings[
                "use_trailing_stop"
            ] = use_trailing_stop

            df["signal"] = df.apply(
                lambda row: generate_signal(
                    row,
                    test_settings
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

                if (
                    position == 0
                    and signal == "BUY"
                ):

                    stop_loss_price = (
                        price
                        - (
                            atr_value
                            * settings[
                                "atr_stop_multiplier"
                            ]
                        )
                    )

                    risk_amount = (
                        balance * risk_per_trade
                    )

                    stop_distance = (
                        price - stop_loss_price
                    )

                    if stop_distance <= 0:
                        continue

                    position_size = (
                        risk_amount
                        / stop_distance
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
                        buy_amount_after_fee
                        / price
                    )

                    entry_price = price
                    highest_price = price

                    balance -= amount_to_spend

                    trades.append((
                        "BUY",
                        row["timestamp"],
                        price,
                        0
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

                    should_sell = False

                    if (
                        use_trailing_stop
                        and price <= trailing_stop
                    ):

                        should_sell = True

                    elif price <= active_stop_loss:

                        should_sell = True

                    elif price >= active_take_profit:

                        should_sell = True

                    elif signal == "SELL":

                        should_sell = True

                    if should_sell:

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

                        balance += (
                            sell_value_after_fee
                        )

                        trades.append((
                            "SELL",
                            row["timestamp"],
                            price,
                            profit
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

            return_pct = (
                (profit / starting_coin_balance)
                * 100
            )

            sell_trades = [
                trade for trade in trades
                if trade[0] == "SELL"
            ]

            winning_trades = [
                trade for trade in sell_trades
                if trade[3] > 0
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

            results.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "risk": risk_per_trade,
                "trailing": use_trailing_stop,
                "return": round(return_pct, 2),
                "win_rate": round(win_rate, 2),
                "drawdown": round(max_drawdown, 2),
                "trades": len(sell_trades),
                "ema200": settings[
                    "use_ema200_filter"
                ]
            })

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="return",
    ascending=False
)

print("\n==============================")
print("OPTIMIZATION RESULTS")
print("==============================")

for _, row in results_df.iterrows():

    print(
        f"{row['symbol']} | "
        f"{row['timeframe']} | "
        f"Risk: {row['risk'] * 100:.0f}% | "
        f"Trailing: {row['trailing']} | "
        f"EMA200: {row['ema200']} | "
        f"Return: {row['return']}% | "
        f"Win Rate: {row['win_rate']}% | "
        f"Drawdown: {row['drawdown']}% | "
        f"Trades: {row['trades']}"
    )