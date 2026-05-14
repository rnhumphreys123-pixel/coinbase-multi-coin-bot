def generate_signal(row, settings):

    ema_20 = row["ema_20"]
    ema_50 = row["ema_50"]
    ema_200 = row["ema_200"]
    rsi = row["rsi"]
    close = row["close"]

    rsi_min = settings["rsi_buy_min"]
    rsi_max = settings["rsi_buy_max"]

    use_ema200_filter = settings.get(
        "use_ema200_filter",
        False
    )

    if use_ema200_filter and close < ema_200:
        return "HOLD"

    if ema_20 > ema_50 and rsi_min <= rsi <= rsi_max:
        return "BUY"

    elif ema_20 < ema_50:
        return "SELL"

    else:
        return "HOLD"