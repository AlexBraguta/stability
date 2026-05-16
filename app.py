"""Streamlit dashboard for the Token Stability scanner.

Pick a quote currency (USDT / USDC), choose which symbols to scan from
the live list pulled off Binance USDⓂ Futures, run the scan, and read
the results sorted with the most "stable" tokens at the top.
"""
import pandas as pd
import streamlit as st

import config
from stability import CANDLE_LIMIT, TIMEFRAMES, get_stability, list_symbols

st.set_page_config(page_title="Token Stability Scanner", page_icon="📊", layout="wide")

st.title("📊 Token Stability Scanner")
st.caption(
    f"Stability = count of past candles whose high/low straddle the current "
    f"price, across {', '.join(TIMEFRAMES)} ({CANDLE_LIMIT} candles each), summed. "
    f"Higher = price has spent more time at this level."
)

CREDS_MISSING = (
    not config.API_KEY
    or not config.API_SECRET
    or config.API_KEY == "your_api_key_here"
)
if CREDS_MISSING:
    st.warning(
        "Binance API credentials are not set. Edit the **.env** file and put "
        "your real `BINANCE_API_KEY` / `BINANCE_API_SECRET` in it, then "
        "restart. Public endpoints may still work without keys.",
        icon="⚠️",
    )


@st.cache_data(show_spinner="Fetching available symbols from Binance…")
def load_symbols(quote):
    return list_symbols(quote)


with st.sidebar:
    st.header("Settings")
    quote = st.radio(
        "Quote currency",
        options=["USDT", "USDC"],
        index=0,
        help="Which pairs to list from the exchange.",
    )

    try:
        all_symbols = load_symbols(quote)
        load_error = None
    except Exception as exc:  # noqa: BLE001 - surface any API/network error to the UI
        all_symbols = []
        load_error = str(exc)

    if load_error:
        st.error(f"Could not load symbols: {load_error}")
    else:
        st.success(f"{len(all_symbols)} {quote} symbols available")

    col_a, col_b = st.columns(2)
    if col_a.button("Select all", use_container_width=True):
        st.session_state.selected = list(all_symbols)
    if col_b.button("Clear", use_container_width=True):
        st.session_state.selected = []

    default_selected = st.session_state.get("selected", list(all_symbols))
    # Drop anything that is no longer valid for the current quote.
    default_selected = [s for s in default_selected if s in all_symbols]

    selected = st.multiselect(
        "Tokens to scan",
        options=all_symbols,
        default=default_selected,
        help="Unselect any token you don't want scanned.",
    )
    st.session_state.selected = selected

    run = st.button(
        f"▶ Run scan ({len(selected)} tokens)",
        type="primary",
        use_container_width=True,
        disabled=not selected,
    )

if run:
    progress_bar = st.progress(0.0, text="Starting…")
    status = st.empty()

    def on_progress(done, total, token, score):
        pct = done / total if total else 1.0
        label = (
            f"{token}: {score}" if score is not None else f"{token}: skipped"
        )
        progress_bar.progress(min(pct, 1.0), text=f"{done}/{total} — {label}")

    with st.spinner("Scanning…"):
        df = get_stability(selected, progress=on_progress)

    progress_bar.empty()
    status.empty()

    if df.empty:
        st.error("No results — every selected token failed or returned no data.")
    else:
        st.session_state.results = df
        st.success(f"Done — scanned {len(df)} tokens.")

if "results" in st.session_state and not st.session_state.results.empty:
    df = st.session_state.results
    st.subheader("Results")

    c1, c2, c3 = st.columns(3)
    c1.metric("Tokens", len(df))
    c2.metric("Most stable", df.iloc[0]["token"], int(df.iloc[0]["stability"]))
    c3.metric("Median score", int(df["stability"].median()))

    ranked = df.reset_index(drop=True).copy()
    ranked.index = ranked.index + 1
    ranked.index.name = "rank"

    st.dataframe(
        ranked,
        use_container_width=True,
        height=600,
        column_config={
            "token": st.column_config.TextColumn("Token"),
            "stability": st.column_config.ProgressColumn(
                "Stability",
                format="%d",
                min_value=0,
                max_value=int(df["stability"].max()),
            ),
        },
    )

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="stability_results.csv",
        mime="text/csv",
    )
