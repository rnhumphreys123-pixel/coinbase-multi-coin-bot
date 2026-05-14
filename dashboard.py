import streamlit as st
import pandas as pd
import json

from config import (
    PORTFOLIO_SETTINGS,
    ACTIVE_SYMBOLS
)

from risk_manager import (
    get_total_exposure,
    get_open_position_count,
    get_portfolio_drawdown
)

st.set_page_config(
    page_title="Coinbase Trading Bot Dashboard",
    layout="wide"
)

STATE_FILE = "state.json"
EQUITY_LOG_FILE = "equity_log.csv"
TRADE_LOG_FILE = "trade_log.csv"
EVENT_LOG_FILE = "events_log.csv"
SIGNALS_LOG_FILE = "signals_log.csv"

st.title("📊 Coinbase Trading Bot Dashboard")
st.caption("Live paper trading command center")

st.sidebar.header("Dashboard Controls")

if st.sidebar.button("Refresh Dashboard"):
    st.rerun()

try:
    with open(STATE_FILE, "r") as file:
        state = json.load(file)
except FileNotFoundError:
    state = {}

try:
    equity_df = pd.read_csv(EQUITY_LOG_FILE, encoding="utf-8-sig")
    equity_df.columns = equity_df.columns.str.strip()
    equity_df["timestamp"] = pd.to_datetime(equity_df["timestamp"])
except FileNotFoundError:
    equity_df = pd.DataFrame()

starting_value = PORTFOLIO_SETTINGS["starting_balance"]

if not equity_df.empty:
    active_equity = equity_df[
        equity_df["symbol"].isin(ACTIVE_SYMBOLS)
    ]

    latest_rows = (
        active_equity
        .sort_values("timestamp")
        .groupby("symbol")
        .tail(1)
    )

    current_value = latest_rows["total_value"].sum()
else:
    active_equity = pd.DataFrame()
    current_value = starting_value

profit = current_value - starting_value
return_pct = (profit / starting_value) * 100

st.header("💼 Portfolio Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Starting Portfolio", f"${starting_value:,.2f}")
col2.metric("Current Portfolio", f"${current_value:,.2f}")
col3.metric("Profit / Loss", f"${profit:,.2f}")
col4.metric("Return", f"{return_pct:.2f}%")

st.header("🛡️ Risk Status")

risk_col1, risk_col2, risk_col3 = st.columns(3)

risk_col1.metric("Total Exposure", f"{get_total_exposure() * 100:.2f}%")
risk_col2.metric("Open Positions", get_open_position_count())
risk_col3.metric("Portfolio Drawdown", f"{get_portfolio_drawdown() * 100:.2f}%")

st.header("🚦 Live Signal Status")

try:
    events_df = pd.read_csv(EVENT_LOG_FILE, encoding="utf-8-sig")
    events_df.columns = events_df.columns.str.strip()

    signal_cols = st.columns(len(ACTIVE_SYMBOLS))

    for index, symbol in enumerate(ACTIVE_SYMBOLS):

        if "symbol" in events_df.columns:
            symbol_events = events_df[
                events_df["symbol"] == symbol
            ]
        else:
            symbol_events = pd.DataFrame()

        latest_event = (
            symbol_events.tail(1)
            if not symbol_events.empty
            else pd.DataFrame()
        )

        if not latest_event.empty:
            latest_message = latest_event.iloc[0].get("message", "No message")
            latest_event_type = latest_event.iloc[0].get("event", "UNKNOWN")
        else:
            latest_message = "No recent event for this symbol"
            latest_event_type = "UNKNOWN"

        with signal_cols[index]:
            st.metric(label=symbol, value=latest_event_type)
            st.caption(latest_message)

except FileNotFoundError:
    st.info("No event log found yet.")

st.header("📡 Live Signal Table")

try:
    signals_df = pd.read_csv(SIGNALS_LOG_FILE, encoding="utf-8-sig")
    signals_df.columns = signals_df.columns.str.strip()
    signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"])

    signals_df = signals_df[
        signals_df["symbol"].isin(ACTIVE_SYMBOLS)
    ]

    latest_signals = (
        signals_df
        .sort_values("timestamp")
        .groupby("symbol")
        .tail(1)
    )

    def signal_color(signal):
        if signal == "BUY":
            return "background-color: #0f5132; color: white"
        elif signal == "SELL":
            return "background-color: #842029; color: white"
        else:
            return "background-color: #6c757d; color: white"

    styled_df = latest_signals.style.map(
        signal_color,
        subset=["signal"]
    )

    st.dataframe(
        styled_df,
        use_container_width=True
    )

except FileNotFoundError:
    st.info("No signals log found yet.")

st.header("📌 Portfolio State")

position_cols = st.columns(len(ACTIVE_SYMBOLS))

for index, symbol in enumerate(ACTIVE_SYMBOLS):

    data = state.get(symbol, {})

    balance = data.get("balance", 0)
    position = data.get("position", 0)
    entry_price = data.get("entry_price", 0)
    highest_price = data.get("highest_price", 0)
    current_price = data.get("current_price", 0)
    trailing_stop = data.get("trailing_stop_price", 0)

    position_value = position * current_price

    unrealized_pnl = (
        (current_price - entry_price) * position
        if position > 0
        else 0
    )

    with position_cols[index]:

        st.subheader(symbol)

        if position > 0:
            st.success("IN POSITION")
        else:
            st.warning("NO POSITION")

        st.metric(
            "Position Value",
            f"${position_value:.2f}"
        )

        pnl_label = "🟢 Profit"

        if unrealized_pnl < 0:
            pnl_label = "🔴 Loss"

        elif unrealized_pnl == 0:
            pnl_label = "⚪ Flat"

        st.metric(
            pnl_label,
            f"${unrealized_pnl:.2f}"
        )

        st.write(f"Entry Price: ${entry_price:.2f}")
        st.write(f"Current Price: ${current_price:.2f}")
        st.write(f"Trailing Stop: ${trailing_stop:.2f}")
        st.write(f"Highest Price: ${highest_price:.2f}")

if state:
    state_rows = []

    for symbol in ACTIVE_SYMBOLS:
        data = state.get(symbol, {})

        state_rows.append({
            "Symbol": symbol,
            "Cash Balance": round(data.get("balance", 0), 2),
            "Position": round(data.get("position", 0), 8),
            "Entry Price": round(data.get("entry_price", 0), 2),
            "Highest Price": round(data.get("highest_price", 0), 2),
            "Current Price": round(data.get("current_price", 0), 2),
            "Trailing Stop": round(data.get("trailing_stop_price", 0), 2),
            "In Position": "Yes" if data.get("position", 0) > 0 else "No"
        })

    state_df = pd.DataFrame(state_rows)

    st.dataframe(
        state_df,
        use_container_width=True
    )

else:
    st.warning("No state data found yet.")

st.header("📈 Equity Curve")

if not equity_df.empty and not active_equity.empty:

    chart_df = active_equity.copy()
    chart_df["label"] = chart_df["symbol"]

    st.line_chart(
        chart_df,
        x="timestamp",
        y="total_value",
        color="label"
    )

    # --------------------------------------------------
    # DRAWDOWN CHART
    # --------------------------------------------------

    drawdown_df = active_equity.copy()
    drawdown_df = drawdown_df.sort_values("timestamp")

    drawdown_df["running_peak"] = (
        drawdown_df["total_value"].cummax()
    )

    drawdown_df["drawdown_pct"] = (
        (
            drawdown_df["total_value"]
            - drawdown_df["running_peak"]
        )
        / drawdown_df["running_peak"]
    ) * 100

    st.subheader("📉 Portfolio Drawdown")

    st.line_chart(
        drawdown_df,
        x="timestamp",
        y="drawdown_pct"
    )

    st.subheader("Latest Equity Entries")

    st.dataframe(
        active_equity.tail(20),
        use_container_width=True
    )

else:
    st.info("No equity log found yet.")

st.header("💰 Recent Trades")

try:
    trades_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
    trades_df.columns = trades_df.columns.str.strip()

    if "symbol" in trades_df.columns:
        trades_df = trades_df[
            trades_df["symbol"].isin(ACTIVE_SYMBOLS)
        ]

    st.dataframe(
        trades_df.tail(20),
        use_container_width=True
    )

except FileNotFoundError:
    st.info("No trade log found yet.")

st.header("🧠 Recent Bot Events")

try:
    events_df = pd.read_csv(EVENT_LOG_FILE, encoding="utf-8-sig")
    events_df.columns = events_df.columns.str.strip()

    if "symbol" in events_df.columns:
        events_df = events_df[
            events_df["symbol"].isin(ACTIVE_SYMBOLS)
        ]

    st.dataframe(
        events_df.tail(20),
        use_container_width=True
    )

except FileNotFoundError:
    st.info("No event log found yet.")

st.caption("Coinbase Multi-Coin Paper Trading Dashboard")