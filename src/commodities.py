"""How sensitive is each energy stock to oil and gas prices?"""

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS


def weekly_returns(prices):
    """Friday-to-Friday returns.

    Stocks close in New York, Brent trades in London and TTF in Amsterdam,
    so their daily closing prices are taken at different times of day.
    Weekly returns make that timing mismatch much less important.
    """
    return prices.resample("W-FRI").last().pct_change().dropna()


def combine(stock_prices, commodity_prices):
    """Put stocks and commodities on the same dates, then go weekly.

    Commodities follow the stock market's calendar; on a stock trading day
    with no commodity price (e.g. a European holiday) we carry the last
    price forward.
    """
    combined = stock_prices.join(commodity_prices, how="left").ffill()
    return weekly_returns(combined)