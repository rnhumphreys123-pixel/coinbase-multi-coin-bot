COIN_CONFIG = {

    "BTC/USD": {
        "timeframe": "6h",
        "allocation": 0.70,

        "rsi_buy_min": 50,
        "rsi_buy_max": 62,

        "atr_stop_multiplier": 2,
        "atr_take_profit_multiplier": 4,

        "risk_per_trade": 0.02,
        "use_trailing_stop": True,

        "coin_drawdown_limit": -0.05,

        "use_ema200_filter": True
    },

    "ETH/USD": {
        "timeframe": "1h",
        "allocation": 0.00,

        "rsi_buy_min": 50,
        "rsi_buy_max": 62,

        "atr_stop_multiplier": 2,
        "atr_take_profit_multiplier": 4,

        "risk_per_trade": 0.01,
        "use_trailing_stop": False,

        "coin_drawdown_limit": -0.05,

        "use_ema200_filter": True
    },

    "SOL/USD": {
        "timeframe": "1h",
        "allocation": 0.30,

        "rsi_buy_min": 50,
        "rsi_buy_max": 62,

        "atr_stop_multiplier": 2,
        "atr_take_profit_multiplier": 4,

        "risk_per_trade": 0.02,
        "use_trailing_stop": False,

        "coin_drawdown_limit": -0.05,

        "use_ema200_filter": True
    }
}


ACTIVE_SYMBOLS = [
    "BTC/USD",
    "SOL/USD"
]


PORTFOLIO_SETTINGS = {
    "starting_balance": 1000
}


RISK_SETTINGS = {
    "daily_loss_limit": -50,
    "max_total_exposure": 0.80,
    "max_open_positions": 2,
    "portfolio_drawdown_limit": -0.05
}