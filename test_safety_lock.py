from config import TRADING_MODE

print("\n==============================")
print("TRADING SAFETY LOCK TEST")
print("==============================")

print(f"Trading Mode: {TRADING_MODE['mode']}")
print(f"Live Trading Enabled: {TRADING_MODE['live_trading_enabled']}")

if TRADING_MODE["mode"] == "PAPER" and not TRADING_MODE["live_trading_enabled"]:
    print("\n✅ Safety lock is active. Bot is PAPER ONLY.")
else:
    print("\n⚠️ WARNING: Live trading may be enabled. Double-check config.py.")