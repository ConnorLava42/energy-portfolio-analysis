"""Testing the optimiser on data it has not seen yet."""

import pandas as pd

from src import optimise

# Each strategy takes past returns and gives back a set of weights
STRATEGIES = {
    "Max Sharpe": optimise.max_sharpe_weights,
    "Max Sharpe (25% cap)": lambda r: optimise.max_sharpe_weights(r, max_weight=0.25),
    "Min variance": optimise.min_variance_weights,
    "Equal weight": lambda r: pd.Series(1 / r.shape[1], index=r.columns),
}


def buy_and_hold(returns, weights):
    """Daily returns of a portfolio bought on day one and then left alone.

    Weights drift as prices move: a stock that rises becomes a bigger share
    of the portfolio. That is what really happens between rebalances.
    """
    value = (1 + returns).cumprod() @ weights[returns.columns]
    daily = value.pct_change()
    daily.iloc[0] = value.iloc[0] - 1  # first day: from $1 to the first value
    return daily


def out_of_sample(returns, split_date):
    """Choose weights using data up to split_date, then hold them after it.

    Returns the weights each strategy picked and each strategy's daily
    returns over the test period.
    """
    train = returns[returns.index <= split_date]
    test = returns[returns.index > split_date]

    weights = pd.DataFrame({name: pick(train) for name, pick in STRATEGIES.items()})
    test_returns = pd.DataFrame(
        {name: buy_and_hold(test, weights[name]) for name in weights}
    )
    return weights, test_returns