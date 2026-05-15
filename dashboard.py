import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import plotly.graph_objects as go
import subprocess

from bot_control import is_bot_paused, set_bot_paused

from config import PORTFOLIO_SETTINGS, ACTIVE_SYMBOLS

from risk_manager import (
    get_total_exposure,
    get_open_position_count,
    get_portfolio_drawdown
)

st.set_page_config(
    page_title="Coinbase Trading Bot Dashboard",
    layout="wide"
)

st.markdown("""
<style>
.main { background-color: #0e1117; }
h1, h2, h3 { color: #f8f9fa; }

section[data-testid="stSidebar"] {
    background-color: #161b22;
}

div[data-testid="metric-container"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

STATE_FILE = "state.json"
EQUITY_LOG_FILE = "equity_log.csv"
TRADE_LOG_FILE = "trade_log.csv"
EVENT_LOG_FILE = "events_log.csv"
SIGNALS_LOG_FILE = "signals_log.csv"
CANDLES_LOG_FILE = "candles_log.csv"

st.title("🚀 Coinbase Multi-Coin Trading Dashboard")
st.caption("Live paper trading command center")

st.sidebar.title("⚙️ Control Panel")
bot_paused = is_bot_paused()

if bot_paused:
    st.sidebar.error("Bot Mode: PAUSED")
else:
    st.sidebar.success("Bot Mode: RUNNING")

if st.sidebar.button("Pause Bot"):
    set_bot_paused(True)
    st.rerun()

if st.sidebar.button("Resume Bot"):
    set_bot_paused(False)
    st.rerun()

st.sidebar.markdown("---")

auto_refresh = st.sidebar.checkbox(
    "Auto Refresh",
    value=False
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh Interval",
    [15, 30, 60],
    index=2
)

if auto_refresh:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="dashboard_auto_refresh"
    )

st.sidebar.markdown("---")

if st.sidebar.button("▶️ Run Bot Now"):

    try:

        subprocess.Popen(
            ["python", "market_data.py"]
        )

        st.sidebar.success(
            "Bot run started."
        )

    except Exception as error:

        st.sidebar.error(
            f"Error: {error}"
        )

st.sidebar.markdown("---")
st.sidebar.write("### Active Symbols")

for symbol in ACTIVE_SYMBOLS:
    st.sidebar.write(f"• {symbol}")

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

overview_tab, charts_tab, analytics_tab, logs_tab, config_tab = st.tabs([
    "💼 Overview",
    "🕯️ Charts",
    "📊 Analytics",
    "📜 Logs",
    "⚙️ Config"
])

with overview_tab:

    st.header("💼 Portfolio Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Starting Portfolio", f"${starting_value:,.2f}")
    col2.metric("Current Portfolio", f"${current_value:,.2f}")
    col3.metric("Profit / Loss", f"${profit:,.2f}")
    col4.metric("Return", f"{return_pct:.2f}%")

    st.header("🛡️ Risk Status")

    r1, r2, r3 = st.columns(3)

    r1.metric("Total Exposure", f"{get_total_exposure() * 100:.2f}%")
    r2.metric("Open Positions", get_open_position_count())
    r3.metric("Portfolio Drawdown", f"{get_portfolio_drawdown() * 100:.2f}%")

    st.header("🧭 Bot Status Panel")

    bot_mode = "PAUSED" if is_bot_paused() else "RUNNING"

    last_signal_time = "No signal data"
    last_candle_time = "No candle data"
    last_trade_time = "No trade data"

    try:
        status_signals_df = pd.read_csv(SIGNALS_LOG_FILE, encoding="utf-8-sig")
        status_signals_df.columns = status_signals_df.columns.str.strip()
        status_signals_df["timestamp"] = pd.to_datetime(status_signals_df["timestamp"])
        last_signal_time = status_signals_df["timestamp"].max()
    except FileNotFoundError:
        pass

    try:
        status_candles_df = pd.read_csv(CANDLES_LOG_FILE, encoding="utf-8-sig")
        status_candles_df.columns = status_candles_df.columns.str.strip()
        status_candles_df["timestamp"] = pd.to_datetime(
        status_candles_df["timestamp"],
             errors="coerce"
        )

        status_candles_df = status_candles_df.dropna(
            subset=["timestamp"]
        )
        last_candle_time = status_candles_df["timestamp"].max()
    except FileNotFoundError:
        pass

    try:
        status_trades_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
        status_trades_df.columns = status_trades_df.columns.str.strip()
        status_trades_df["timestamp"] = pd.to_datetime(status_trades_df["timestamp"])
        last_trade_time = status_trades_df["timestamp"].max()
    except FileNotFoundError:
        pass

    def format_time(value):
        if isinstance(value, str):
            return value

        try:
            return pd.to_datetime(value).strftime("%m-%d %H:%M")
        except:
            return str(value)

    s1, s2, s3, s4 = st.columns(4)

    s1.metric("Bot Mode", bot_mode)
    s2.metric("Last Signal", format_time(last_signal_time))
    s3.metric("Last Candle", format_time(last_candle_time))
    s4.metric("Last Trade", format_time(last_trade_time))

    st.header("📌 Open Positions")

    position_cols = st.columns(len(ACTIVE_SYMBOLS))

    for index, symbol in enumerate(ACTIVE_SYMBOLS):

        data = state.get(symbol, {})

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

            st.metric("Position Value", f"${position_value:.2f}")

            pnl_label = "🟢 Profit"

            if unrealized_pnl < 0:
                pnl_label = "🔴 Loss"
            elif unrealized_pnl == 0:
                pnl_label = "⚪ Flat"

            st.metric(pnl_label, f"${unrealized_pnl:.2f}")

            st.write(f"Entry Price: ${entry_price:.2f}")
            st.write(f"Current Price: ${current_price:.2f}")
            st.write(f"Trailing Stop: ${trailing_stop:.2f}")
            st.write(f"Highest Price: ${highest_price:.2f}")

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
                latest_message = "No recent event"
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

        st.dataframe(styled_df, use_container_width=True)

    except FileNotFoundError:
        st.info("No signals log found yet.")


with charts_tab:

    st.header("🕯️ Candlestick Charts")

    try:
        candles_df = pd.read_csv(CANDLES_LOG_FILE, encoding="utf-8-sig")
        candles_df.columns = candles_df.columns.str.strip()
        candles_df["timestamp"] = pd.to_datetime(candles_df["timestamp"])

        candles_df = candles_df[
            candles_df["symbol"].isin(ACTIVE_SYMBOLS)
        ]

        try:
            trades_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
            trades_df.columns = trades_df.columns.str.strip()

            if "timestamp" in trades_df.columns:
                trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])

        except FileNotFoundError:
            trades_df = pd.DataFrame()

        for symbol in ACTIVE_SYMBOLS:

            symbol_df = candles_df[
                candles_df["symbol"] == symbol
            ].copy()

            if symbol_df.empty:
                continue

            symbol_df = symbol_df.sort_values("timestamp").tail(120)

            st.subheader(symbol)

            fig = go.Figure()

            fig.add_trace(
                go.Candlestick(
                    x=symbol_df["timestamp"],
                    open=symbol_df["open"],
                    high=symbol_df["high"],
                    low=symbol_df["low"],
                    close=symbol_df["close"],
                    name=symbol
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=symbol_df["timestamp"],
                    y=symbol_df["ema_20"],
                    mode="lines",
                    name="EMA 20"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=symbol_df["timestamp"],
                    y=symbol_df["ema_50"],
                    mode="lines",
                    name="EMA 50"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=symbol_df["timestamp"],
                    y=symbol_df["ema_200"],
                    mode="lines",
                    name="EMA 200"
                )
            )

            if not trades_df.empty and "symbol" in trades_df.columns:

                symbol_trades = trades_df[
                    trades_df["symbol"] == symbol
                ].copy()

                buys = symbol_trades[
                    symbol_trades["action"] == "BUY"
                ]

                sells = symbol_trades[
                    symbol_trades["action"] == "SELL"
                ]

                if not buys.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=buys["timestamp"],
                            y=buys["price"],
                            mode="markers",
                            marker=dict(
                                symbol="triangle-up",
                                size=14,
                                color="lime"
                            ),
                            name="BUY"
                        )
                    )

                if not sells.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=sells["timestamp"],
                            y=sells["price"],
                            mode="markers",
                            marker=dict(
                                symbol="triangle-down",
                                size=14,
                                color="red"
                            ),
                            name="SELL"
                        )
                    )

            fig.update_layout(
                height=500,
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(fig, use_container_width=True)

    except FileNotFoundError:
        st.info("No candle log found yet.")

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


with analytics_tab:

    st.header("📊 Strategy Analytics")

    try:
        analytics_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
        analytics_df.columns = analytics_df.columns.str.strip()

        if "symbol" in analytics_df.columns:
            analytics_df = analytics_df[
                analytics_df["symbol"].isin(ACTIVE_SYMBOLS)
            ]

        sells_df = analytics_df[
            analytics_df["action"] == "SELL"
        ].copy()

        if not sells_df.empty:

            sells_df["profit"] = sells_df["profit"].astype(float)

            total_trades = len(sells_df)
            wins = sells_df[sells_df["profit"] > 0]
            losses = sells_df[sells_df["profit"] <= 0]

            win_rate = (len(wins) / total_trades) * 100
            total_profit = sells_df["profit"].sum()
            average_win = wins["profit"].mean() if not wins.empty else 0
            average_loss = losses["profit"].mean() if not losses.empty else 0
            best_trade = sells_df["profit"].max()
            worst_trade = sells_df["profit"].min()

            gross_profit = wins["profit"].sum()
            gross_loss = abs(losses["profit"].sum())

            profit_factor = (
                gross_profit / gross_loss
                if gross_loss > 0
                else 0
            )

            a1, a2, a3, a4 = st.columns(4)

            a1.metric("Completed Trades", total_trades)
            a2.metric("Win Rate", f"{win_rate:.2f}%")
            a3.metric("Total Profit", f"${total_profit:.2f}")
            a4.metric("Profit Factor", f"{profit_factor:.2f}")

            b1, b2, b3, b4 = st.columns(4)

            b1.metric("Average Win", f"${average_win:.2f}")
            b2.metric("Average Loss", f"${average_loss:.2f}")
            b3.metric("Best Trade", f"${best_trade:.2f}")
            b4.metric("Worst Trade", f"${worst_trade:.2f}")

            win_loss_fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Wins", "Losses"],
                        values=[len(wins), len(losses)],
                        hole=0.45
                    )
                ]
            )

            win_loss_fig.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(win_loss_fig, use_container_width=True)

        else:
            st.info("No completed sell trades yet.")

    except FileNotFoundError:
        st.info("No trade log found yet.")

    st.header("🪙 Per-Symbol Analytics")

    try:
        symbol_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
        symbol_df.columns = symbol_df.columns.str.strip()

        symbol_df = symbol_df[
            symbol_df["symbol"].isin(ACTIVE_SYMBOLS)
        ]

        sells_by_symbol = symbol_df[
            symbol_df["action"] == "SELL"
        ].copy()

        if not sells_by_symbol.empty:

            sells_by_symbol["profit"] = sells_by_symbol["profit"].astype(float)

            for symbol in ACTIVE_SYMBOLS:

                coin_sells = sells_by_symbol[
                    sells_by_symbol["symbol"] == symbol
                ]

                if coin_sells.empty:
                    continue

                wins = coin_sells[coin_sells["profit"] > 0]
                losses = coin_sells[coin_sells["profit"] <= 0]

                total_trades = len(coin_sells)
                win_rate = (len(wins) / total_trades) * 100
                total_profit = coin_sells["profit"].sum()
                average_win = wins["profit"].mean() if not wins.empty else 0
                average_loss = losses["profit"].mean() if not losses.empty else 0

                gross_profit = wins["profit"].sum()
                gross_loss = abs(losses["profit"].sum())

                profit_factor = (
                    gross_profit / gross_loss
                    if gross_loss > 0
                    else 0
                )

                st.subheader(symbol)

                c1, c2, c3, c4, c5 = st.columns(5)

                c1.metric("Trades", total_trades)
                c2.metric("Win Rate", f"{win_rate:.2f}%")
                c3.metric("Profit", f"${total_profit:.2f}")
                c4.metric("Profit Factor", f"{profit_factor:.2f}")
                c5.metric("Avg Win / Loss", f"${average_win:.2f} / ${average_loss:.2f}")

        else:
            st.info("No completed sell trades yet.")

    except FileNotFoundError:
        st.info("No trade log found yet.")

    st.header("🚪 Exit Reason Analytics")

    try:
        exit_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
        exit_df.columns = exit_df.columns.str.strip()

        if "symbol" in exit_df.columns:
            exit_df = exit_df[
                exit_df["symbol"].isin(ACTIVE_SYMBOLS)
            ]

        sells = exit_df[
            exit_df["action"] == "SELL"
        ].copy()

        if not sells.empty and "reason" in sells.columns:

            sells["profit"] = sells["profit"].astype(float)
            sells["reason"] = sells["reason"].fillna("Unknown / Old Trade")

            reason_summary = sells.groupby("reason").agg(
                trades=("profit", "count"),
                total_profit=("profit", "sum"),
                average_profit=("profit", "mean"),
                wins=("profit", lambda x: (x > 0).sum()),
                losses=("profit", lambda x: (x <= 0).sum())
            ).reset_index()

            st.dataframe(reason_summary, use_container_width=True)

            reason_fig = go.Figure()

            reason_fig.add_trace(
                go.Bar(
                    x=reason_summary["reason"],
                    y=reason_summary["total_profit"],
                    name="Total Profit"
                )
            )

            reason_fig.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(reason_fig, use_container_width=True)

        else:
            st.info("No exit reason data yet.")

    except FileNotFoundError:
        st.info("No trade log found yet.")

    st.header("📈 Equity Growth Analytics")

    try:
        growth_df = pd.read_csv(EQUITY_LOG_FILE, encoding="utf-8-sig")
        growth_df.columns = growth_df.columns.str.strip()
        growth_df["timestamp"] = pd.to_datetime(growth_df["timestamp"])

        growth_df = growth_df[
            growth_df["symbol"].isin(ACTIVE_SYMBOLS)
        ]

        portfolio_growth = (
            growth_df
            .groupby("timestamp")["total_value"]
            .sum()
            .reset_index()
        )

        portfolio_growth = portfolio_growth.sort_values("timestamp")

        portfolio_growth["cumulative_return_pct"] = (
            (
                portfolio_growth["total_value"]
                - starting_value
            )
            / starting_value
        ) * 100

        growth_fig = go.Figure()

        growth_fig.add_trace(
            go.Scatter(
                x=portfolio_growth["timestamp"],
                y=portfolio_growth["cumulative_return_pct"],
                mode="lines",
                name="Portfolio Growth %"
            )
        )

        growth_fig.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="Return %",
            xaxis_title="Time"
        )

        st.plotly_chart(growth_fig, use_container_width=True)

    except FileNotFoundError:
        st.info("No equity growth data found yet.")


with logs_tab:

    st.header("💰 Trade Log")

    try:
        trades_df = pd.read_csv(TRADE_LOG_FILE, encoding="utf-8-sig")
        trades_df.columns = trades_df.columns.str.strip()

        if "symbol" in trades_df.columns:
            trades_df = trades_df[
                trades_df["symbol"].isin(ACTIVE_SYMBOLS)
            ]

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            selected_symbol = st.selectbox(
                "Filter by Symbol",
                ["All"] + ACTIVE_SYMBOLS
            )

        with filter_col2:
            selected_action = st.selectbox(
                "Filter by Action",
                ["All", "BUY", "SELL"]
            )

        with filter_col3:
            row_limit = st.selectbox(
                "Rows to Show",
                [10, 25, 50, 100],
                index=2
            )

        filtered_trades = trades_df.copy()

        if selected_symbol != "All":
            filtered_trades = filtered_trades[
                filtered_trades["symbol"] == selected_symbol
            ]

        if selected_action != "All":
            filtered_trades = filtered_trades[
                filtered_trades["action"] == selected_action
            ]

        if "reason" in filtered_trades.columns:
            reasons = (
                filtered_trades["reason"]
                .fillna("Unknown / Blank")
                .unique()
                .tolist()
            )

            selected_reason = st.selectbox(
                "Filter by Exit Reason",
                ["All"] + reasons
            )

            if selected_reason != "All":
                filtered_trades = filtered_trades[
                    filtered_trades["reason"].fillna("Unknown / Blank")
                    == selected_reason
                ]

        st.dataframe(
            filtered_trades.tail(row_limit),
            use_container_width=True
        )

    except FileNotFoundError:
        st.info("No trade log found yet.")

with config_tab:

    st.header("⚙️ Bot Configuration")

    from config import COIN_CONFIG, RISK_SETTINGS, PORTFOLIO_SETTINGS

    st.subheader("Portfolio Settings")

    portfolio_df = pd.DataFrame([
        {
            "Starting Balance": PORTFOLIO_SETTINGS["starting_balance"]
        }
    ])

    st.dataframe(
        portfolio_df,
        use_container_width=True
    )

    st.subheader("Coin Settings")

    coin_rows = []

    for symbol, settings in COIN_CONFIG.items():

        coin_rows.append({
            "Symbol": symbol,
            "Active": "Yes" if symbol in ACTIVE_SYMBOLS else "No",
            "Timeframe": settings["timeframe"],
            "Allocation": f"{settings['allocation'] * 100:.0f}%",
            "Risk Per Trade": f"{settings['risk_per_trade'] * 100:.2f}%",
            "Trailing Stop": settings["use_trailing_stop"],
            "EMA 200 Filter": settings["use_ema200_filter"],
            "ATR Stop": settings["atr_stop_multiplier"],
            "ATR Take Profit": settings["atr_take_profit_multiplier"],
            "Coin Drawdown Limit": f"{settings['coin_drawdown_limit'] * 100:.2f}%"
        })

    coin_df = pd.DataFrame(coin_rows)

    st.dataframe(
        coin_df,
        use_container_width=True
    )

    st.subheader("Risk Settings")

    risk_rows = []

    for key, value in RISK_SETTINGS.items():

        risk_rows.append({
            "Setting": key,
            "Value": value
        })

    risk_df = pd.DataFrame(risk_rows)

    st.dataframe(
        risk_df,
        use_container_width=True
    )

    st.header("🧠 Event Log")

    try:
        events_df = pd.read_csv(EVENT_LOG_FILE, encoding="utf-8-sig")
        events_df.columns = events_df.columns.str.strip()

        if "symbol" in events_df.columns:
            events_df = events_df[
                events_df["symbol"].isin(ACTIVE_SYMBOLS)
            ]

        event_col1, event_col2 = st.columns(2)

        with event_col1:
            selected_event_symbol = st.selectbox(
                "Filter Events by Symbol",
                ["All"] + ACTIVE_SYMBOLS
            )

        with event_col2:
            event_row_limit = st.selectbox(
                "Event Rows to Show",
                [10, 25, 50, 100],
                index=2
            )

        filtered_events = events_df.copy()

        if selected_event_symbol != "All":
            filtered_events = filtered_events[
                filtered_events["symbol"] == selected_event_symbol
            ]

        st.dataframe(
            filtered_events.tail(event_row_limit),
            use_container_width=True
        )

    except FileNotFoundError:
        st.info("No event log found yet.")

    st.header("🧠 Recent Bot Events")

    try:
        events_df = pd.read_csv(EVENT_LOG_FILE, encoding="utf-8-sig")
        events_df.columns = events_df.columns.str.strip()

        if "symbol" in events_df.columns:
            events_df = events_df[
                events_df["symbol"].isin(ACTIVE_SYMBOLS)
            ]

        st.dataframe(
            events_df.tail(50),
            use_container_width=True
        )

    except FileNotFoundError:
        st.info("No event log found yet.")

st.markdown("---")
st.caption("Coinbase Multi-Coin Paper Trading Dashboard")