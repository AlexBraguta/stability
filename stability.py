"""v.1.0.1

Core stability logic, shared by the console program (main.py) and the
Streamlit dashboard (app.py).

Stability = for each token, count how many of the past candles had the
current price between their high and low, across 3 timeframes
(1h, 4h, 1d), 1500 candles each, then sum the three counts.
A higher score means the price has spent more time at its current level.
"""
from datetime import datetime

import numpy as np
import pandas as pd
from binance.um_futures import UMFutures

import config

CANDLE_LIMIT = 1500
TIMEFRAMES = ("1d", "4h", "1h")

client = UMFutures(config.API_KEY, config.API_SECRET)


def get_price(token):
    """Current price for a token."""
    ticker = client.ticker_price(token)
    return float(ticker["price"])


def _fmt_time(server_time):
    return datetime.fromtimestamp(int(server_time) / 1000).strftime("%d.%m.%Y %H:%M:%S")


def get_candles(symbol, chart, nr_candles):
    """A given number of candles on a given timeframe for a symbol."""
    response = client.klines(symbol=symbol, interval=chart, limit=nr_candles)
    for item in response:
        item[0] = str(_fmt_time(item[0]))
    return response


def list_symbols(quote=None):
    """All tradable perpetual symbols on USDⓂ Futures.

    quote: 'USDT', 'USDC', or None for everything. Only symbols whose
    status is TRADING are returned, sorted alphabetically.
    """
    info = client.exchange_info()
    symbols = [
        s["symbol"]
        for s in info["symbols"]
        if s.get("status") == "TRADING"
    ]
    if quote:
        symbols = [s for s in symbols if s.endswith(quote)]
    return sorted(symbols)


def _sort_df(candles):
    orig_data = pd.DataFrame(candles)
    convert_dict = {0: str, 1: float, 2: float, 3: float, 4: float}
    data = orig_data.astype(convert_dict)
    ohlc_data = data.iloc[:, [0, 1, 2, 3, 4]].copy()
    return ohlc_data.rename(
        columns={0: "time", 1: "open", 2: "high", 3: "low", 4: "close"}
    )


def stability(token):
    """Stability score for a single token (sum across the 3 timeframes)."""
    total = 0
    price = get_price(token)
    for tf in TIMEFRAMES:
        df = _sort_df(get_candles(token, tf, CANDLE_LIMIT))
        df["passed"] = np.where((price < df["high"]) & (price > df["low"]), 1, 0)
        total += int(df["passed"].sum())
    return total


def get_stability(tokens, progress=None):
    """Stability for a list of tokens, sorted highest first.

    progress: optional callback(done, total, token, score) called after
    each token, used by the dashboard to show progress.
    """
    data = {"token": [], "stability": []}
    df = pd.DataFrame(data)

    iteration = 0
    total = len(tokens)
    for token in tokens:
        try:
            curr_stability = stability(token)
            df.loc[iteration] = [token, curr_stability]
            iteration += 1
            if progress:
                progress(iteration, total, token, curr_stability)
            else:
                print(f"{token}: {curr_stability}")
        except KeyError:
            if progress:
                progress(iteration, total, token, None)

    if not df.empty:
        df.sort_values("stability", ascending=False, inplace=True)
        df["stability"] = df["stability"].astype(int)
        df.reset_index(drop=True, inplace=True)
    return df
