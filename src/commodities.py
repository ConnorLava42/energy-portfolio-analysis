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

def commodity_betas(weekly, stocks, factors):
    """Regress each stock's weekly return on the market and the commodities.

    stock = alpha + b_market * market + b_oil * oil + b_gas * gas + noise

    Including the market means each commodity beta measures the effect of
    oil or gas beyond what the stock market as a whole was doing.
    Returns betas, t-statistics and R-squared, one row per stock.
    """
    X = sm.add_constant(weekly[factors])
    betas, tstats, r2 = {}, {}, {}
    for stock in stocks:
        model = sm.OLS(weekly[stock], X).fit()
        betas[stock] = model.params.drop("const")
        tstats[stock] = model.tvalues.drop("const")
        r2[stock] = model.rsquared
    return (pd.DataFrame(betas).T, pd.DataFrame(tstats).T,
            pd.Series(r2, name="R-squared"))
    
def rolling_betas(weekly, stocks, factors, window=52):
    """The same regression re-estimated over a moving 52-week window.

    Returns a DataFrame with two column levels: (stock, factor).
    """
    X = sm.add_constant(weekly[factors])
    fits = {stock: RollingOLS(weekly[stock], X, window=window).fit().params
            for stock in stocks}
    return pd.concat(fits, axis=1)