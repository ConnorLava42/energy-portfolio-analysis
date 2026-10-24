"""Portfolio optimisation: random portfolios and the efficient frontier.

A portfolio is a set of weights that sum to 1 (e.g. 30% XOM, 70% NEE).
We only allow long positions, so every weight is between 0 and 1.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.config import RISK_FREE_RATE, TRADING_DAYS


def annual_inputs(returns):
    """Expected annual return per stock and the annual covariance matrix."""
    mean_returns = returns.mean() * TRADING_DAYS
    cov = returns.cov() * TRADING_DAYS
    return mean_returns, cov


def single_stock_points(returns):
    """Each stock on its own, measured the same way as the portfolios."""
    mean_returns, cov = annual_inputs(returns)
    return pd.DataFrame({"Return": mean_returns,
                         "Volatility": np.sqrt(np.diag(cov))})


def portfolio_performance(weights, mean_returns, cov):
    """Return (annual return, annual volatility, Sharpe) for one portfolio."""
    ret = weights @ mean_returns
    vol = np.sqrt(weights @ cov @ weights)  # sqrt(w^T * Cov * w)
    return ret, vol, (ret - RISK_FREE_RATE) / vol


def random_portfolios(returns, n=10_000, seed=42):
    """Generate n random long-only portfolios, to see the feasible region."""
    rng = np.random.default_rng(seed)  # fixed seed = same result every run
    mean_returns, cov = annual_inputs(returns)
    weights = rng.dirichlet(np.ones(len(mean_returns)), size=n)  # rows sum to 1

    results = [portfolio_performance(w, mean_returns, cov) for w in weights]
    return pd.DataFrame(results, columns=["Return", "Volatility", "Sharpe"])


def _optimise(objective, n_assets, extra_constraints=(), max_weight=1.0):
    """Shared SciPy call: weights sum to 1, each between 0 and max_weight."""
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    constraints += list(extra_constraints)
    result = minimize(
        objective,
        x0=np.full(n_assets, 1 / n_assets),  # start from equal weights
        method="SLSQP",
        bounds=[(0, max_weight)] * n_assets,
        constraints=constraints,
    )
    if not result.success:
        raise RuntimeError(f"Optimiser failed: {result.message}")
    return result.x


def max_sharpe_weights(returns, max_weight=1.0):
    """Weights with the highest Sharpe ratio (minimise negative Sharpe)."""
    mean_returns, cov = annual_inputs(returns)
    objective = lambda w: -portfolio_performance(w, mean_returns, cov)[2]
    w = _optimise(objective, len(mean_returns), max_weight=max_weight)
    return pd.Series(w, index=returns.columns)


def min_variance_weights(returns, max_weight=1.0):
    """Weights with the lowest possible volatility."""
    mean_returns, cov = annual_inputs(returns)
    objective = lambda w: portfolio_performance(w, mean_returns, cov)[1]
    w = _optimise(objective, len(mean_returns), max_weight=max_weight)
    return pd.Series(w, index=returns.columns)


def efficient_frontier(returns, n_points=40, max_weight=1.0):
    """For a range of target returns, find the lowest-volatility portfolio."""
    mean_returns, cov = annual_inputs(returns)
    n = len(mean_returns)
    vol = lambda w: portfolio_performance(w, mean_returns, cov)[1]

    # Targets run from the min-variance portfolio's return up to the highest
    # return any allowed portfolio can reach
    low = min_variance_weights(returns, max_weight).values @ mean_returns
    high = _optimise(lambda w: -(w @ mean_returns), n, max_weight=max_weight) @ mean_returns

    points = []
    for target in np.linspace(low, high, n_points):
        hit_target = {"type": "eq", "fun": lambda w, t=target: w @ mean_returns - t}
        try:
            w = _optimise(vol, n, [hit_target], max_weight)
        except RuntimeError:
            continue  # some targets are unreachable with a weight cap
        points.append((target, vol(w)))
    return pd.DataFrame(points, columns=["Return", "Volatility"])