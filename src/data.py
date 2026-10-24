"""Download daily prices once, then load them from a local CSV afterwards."""

import pandas as pd
import yfinance as yf

from src.config import BENCHMARK, DATA_DIR, END_DATE, START_DATE, TICKERS


def download_prices(tickers, start, end):
    """Download adjusted daily closing prices from Yahoo Finance.

    auto_adjust=True folds dividends and splits into the price, so a
    percentage change in this series is the stock's total return.
    """
    raw = yf.download(tickers, start=start, end=end,
                      auto_adjust=True, progress=False)
    prices = raw["Close"]  # keep only closing prices: one column per ticker

    missing = [t for t in tickers if t not in prices or prices[t].isna().all()]
    if missing:
        raise ValueError(f"No data came back for: {missing}. "
                         "Check the tickers on finance.yahoo.com.")
    return prices


def load_prices(refresh=False):
    """Return a DataFrame of prices (rows = dates, columns = tickers).

    The first call downloads and saves data/prices.csv. Later calls read
    that file, which is faster and means your results don't shift every
    time Yahoo revises a number. Pass refresh=True to download again.
    """
    cache = DATA_DIR / "prices.csv"
    columns = TICKERS + [BENCHMARK]  # keep the sector order from config.py
    if cache.exists() and not refresh:
        return pd.read_csv(cache, index_col=0, parse_dates=True)[columns]

    DATA_DIR.mkdir(exist_ok=True)
    prices = download_prices(columns, START_DATE, END_DATE)[columns]
    prices.to_csv(cache)
    return prices