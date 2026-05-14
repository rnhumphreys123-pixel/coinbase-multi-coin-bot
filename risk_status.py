from risk_manager import (
    get_total_exposure,
    get_open_position_count,
    get_portfolio_drawdown,
    get_coin_drawdown,
    trading_allowed
)

from config import ACTIVE_SYMBOLS


print("\n==============================")
print("RISK STATUS REPORT")
print("==============================")

print(f"Total Exposure: {get_total_exposure() * 100:.2f}%")
print(f"Open Positions: {get_open_position_count()}")
print(f"Portfolio Drawdown: {get_portfolio_drawdown() * 100:.2f}%")

print("\nBy Symbol:")

for symbol in ACTIVE_SYMBOLS:

    allowed, reason = trading_allowed(symbol)

    print(f"\n{symbol}")
    print(f"Coin Drawdown: {get_coin_drawdown(symbol) * 100:.2f}%")
    print(f"Trading Allowed: {allowed}")
    print(f"Reason: {reason}")