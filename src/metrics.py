"""Return and risk metrics. Every function takes daily data and annualises it."""

import numpy as np
import pandas as pd

from src.config import RISK_FREE_RATE, TRADING_DAYS


def clean_prices(prices, max_missing=0.05):
    """Drop tickers with too much missing data, then fill small gaps.

    Gaps come from things like a UK holiday on a US trading day.
    Forward-filling means "the price didn't change that day".
    """
    share_missing = prices.isna().mean()
    dropped = share_missing[share_missing > max_missing].index.tolist()
    if dropped:
        print(f"Dropping (over {max_missing:.0%} missing): {dropped}")
    return prices.drop(columns=dropped).ffill().dropna()


def daily_returns(prices):
    """Simple daily returns: (today / yesterday) - 1."""
    return prices.pct_change().dropna()

def annualised_return(returns):
    """Compound annual growth rate implied by the daily returns."""
    growth = (1 + returns).prod()
    years = len(returns) / TRADING_DAYS
    return growth ** (1 / years) - 1


def annualised_volatility(returns):
    """Standard deviation of daily returns, scaled up to a year.

    Volatility grows with the square root of time, hence sqrt(252).
    """
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns, risk_free=RISK_FREE_RATE):
    """Return earned above the risk-free rate, per unit of volatility."""
    return (annualised_return(returns) - risk_free) / annualised_volatility(returns)


def max_drawdown(returns):
    """Worst fall from a previous peak, e.g. -0.45 means a 45% drop."""
    wealth = (1 + returns).cumprod()
    running_peak = wealth.cummax()
    return (wealth / running_peak - 1).min()


def beta(returns, market):
    """How much a stock moves for each 1% move in the market.

    beta = covariance(stock, market) / variance(market)
    """
    return returns.apply(lambda col: col.cov(market) / market.var())


def summary_table(returns, market):
    """One row per ticker with every metric, sorted by Sharpe ratio."""
    table = pd.DataFrame({
        "Annual return": annualised_return(returns),
        "Volatility": annualised_volatility(returns),
        "Sharpe": sharpe_ratio(returns),
        "Max drawdown": max_drawdown(returns),
        "Beta": beta(returns, market),
    })
    return table.sort_values("Sharpe", ascending=False)