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

def rolling_backtest(returns, lookback_years=2, freq="QS"):
    """Re-optimise at the start of every quarter on the previous few years.

    Each rebalance only sees data from before that date, so the strategy
    never peeks at the future. Returns each strategy's daily returns and
    the max-Sharpe weights chosen at every rebalance.
    """
    first = (returns.index[0] + pd.DateOffset(years=lookback_years)).to_period("Q").start_time
    rebalance_dates = pd.date_range(first, returns.index[-1], freq=freq)

    pieces = {name: [] for name in STRATEGIES}
    weight_history = {}
    for i, start in enumerate(rebalance_dates):
        is_last = i + 1 == len(rebalance_dates)
        end = returns.index[-1] + pd.Timedelta(days=1) if is_last else rebalance_dates[i + 1]

        window_start = start - pd.DateOffset(years=lookback_years)
        train = returns[(returns.index >= window_start) & (returns.index < start)]
        hold = returns[(returns.index >= start) & (returns.index < end)]

        for name, pick in STRATEGIES.items():
            w = pick(train)
            pieces[name].append(buy_and_hold(hold, w))
            if name == "Max Sharpe":
                weight_history[start] = w

    results = pd.DataFrame({name: pd.concat(p) for name, p in pieces.items()})
    return results, pd.DataFrame(weight_history).T