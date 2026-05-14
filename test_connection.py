import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.coinbase({
    "apiKey": os.getenv("COINBASE_API_KEY"),
    "secret": os.getenv("COINBASE_API_SECRET"),
})

markets = exchange.load_markets()

print("Connected successfully!")
print(f"Loaded {len(markets)} markets")