"""Every chart in the project. Each function can save a PNG to figures/."""

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.ticker as mtick
import seaborn as sns
from matplotlib.lines import Line2D

from src.config import (BENCHMARK, FIG_DIR, SECTOR_COLOURS, SECTORS,
                        TICKER_SECTOR, TRADING_DAYS)

sns.set_theme(style="whitegrid", context="notebook")


def _save(fig, name):
    """Save a figure to figures/<name>.png if a name was given."""
    if name:
        FIG_DIR.mkdir(exist_ok=True)
        fig.savefig(FIG_DIR / f"{name}.png", dpi=150, bbox_inches="tight")


def _sector_legend(ax, include_benchmark=False, loc="best"):
    """A legend with one entry per sector rather than one per ticker."""
    labels = list(SECTORS) + (["Benchmark"] if include_benchmark else [])
    handles = [Line2D([0], [0], color=SECTOR_COLOURS[s], lw=3) for s in labels]
    ax.legend(handles, labels, loc=loc, frameon=True, framealpha=0.9)


def plot_cumulative_returns(returns, market, save_as=None):
    """Growth of $1 invested at the start, one line per stock."""
    fig, ax = plt.subplots(figsize=(11, 6))
    growth = (1 + returns).cumprod()
    for ticker in growth:
        colour = SECTOR_COLOURS[TICKER_SECTOR[ticker]]
        ax.plot(growth.index, growth[ticker], color=colour, lw=1.2, alpha=0.8)
        ax.annotate(ticker, (growth.index[-1], growth[ticker].iloc[-1]),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=colour, va="center")
    ax.plot((1 + market).cumprod(), color=SECTOR_COLOURS["Benchmark"],
            lw=2.5, ls="--")
    ax.axhline(1, color="black", lw=0.8)
    ax.set(title=f"Growth of $1 (dashed = {BENCHMARK})", ylabel="Value of $1")
    _sector_legend(ax, include_benchmark=True, loc="upper left")
    _save(fig, save_as)
    return fig


def plot_correlation_heatmap(returns, save_as=None):
    """Correlation of daily returns, tickers ordered by sector."""
    order = [t for group in SECTORS.values() for t in group if t in returns]
    corr = returns[order].corr()
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
                square=True, cbar_kws={"label": "Correlation"},
                annot_kws={"size": 8}, ax=ax)
    # Thin lines between sectors make the blocks easy to see
    edge = 0
    for group in SECTORS.values():
        edge += len([t for t in group if t in corr])
        ax.axhline(edge, color="white", lw=3)
        ax.axvline(edge, color="white", lw=3)
    ax.set_title("Daily return correlations")
    _save(fig, save_as)
    return fig


def plot_risk_return(summary, save_as=None):
    """Each stock placed by volatility (x) and annual return (y)."""
    fig, ax = plt.subplots(figsize=(9, 6))
    for ticker, row in summary.iterrows():
        colour = SECTOR_COLOURS[TICKER_SECTOR.get(ticker, "Benchmark")]
        ax.scatter(row["Volatility"], row["Annual return"], s=80, color=colour)
        ax.annotate(ticker, (row["Volatility"], row["Annual return"]),
                    xytext=(5, 4), textcoords="offset points", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set(title="Risk vs return", xlabel="Annual volatility",
           ylabel="Annual return")
    _sector_legend(ax, include_benchmark=True)
    _save(fig, save_as)
    return fig

def plot_rolling_volatility(returns, window=63, save_as=None):
    """Average rolling volatility per sector (63 trading days = ~3 months)."""
    rolling = returns.rolling(window).std() * TRADING_DAYS ** 0.5
    fig, ax = plt.subplots(figsize=(11, 5))
    for sector, group in SECTORS.items():
        cols = [t for t in group if t in rolling]
        ax.plot(rolling[cols].mean(axis=1), color=SECTOR_COLOURS[sector],
                lw=2, label=sector)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set(title=f"Rolling {window}-day volatility, sector average",
           ylabel="Annualised volatility")
    ax.legend(frameon=False)
    _save(fig, save_as)
    return fig

def plot_efficient_frontier(random_ports, frontier, special, summary,
                            save_as=None):
    """Random portfolios, the frontier, and the highlighted optimal ones.

    special: dict of label -> (volatility, return), e.g. the max-Sharpe point.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    pts = ax.scatter(random_ports["Volatility"], random_ports["Return"],
                     c=random_ports["Sharpe"], cmap="viridis", s=4, alpha=0.5)
    fig.colorbar(pts, ax=ax, label="Sharpe ratio")
    ax.plot(frontier["Volatility"], frontier["Return"], color="black", lw=2.5,
            label="Efficient frontier")
    for ticker, row in summary.iterrows():  # the single stocks, for reference
        ax.scatter(row["Volatility"], row["Return"], marker="x", color="grey")
        ax.annotate(ticker, (row["Volatility"], row["Return"]),
                    xytext=(4, 3), textcoords="offset points", fontsize=8,
                    color="grey")
    for (label, (vol, ret)), marker in zip(special.items(), ["*", "D", "o"]):
        ax.scatter(vol, ret, marker=marker, s=250, color="crimson",
                   edgecolor="white", zorder=5, label=label)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set(title="Efficient frontier of energy stocks",
           xlabel="Annual volatility", ylabel="Expected annual return")
    ax.legend(loc="lower right", frameon=True, framealpha=0.9)
    _save(fig, save_as)
    return fig

# ---------------------------------------------------------------- backtesting plot

STRATEGY_COLOURS = {
    "Max Sharpe": "#c0392b",
    "Max Sharpe (25% cap)": "#e67e22",
    "Min variance": "#2e8b57",
    "Equal weight": "#1f4e79",
}


def plot_strategy_growth(strategy_returns, market, title, save_as=None):
    """Growth of $1 for each strategy, with the S&P 500 dashed."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    growth = (1 + strategy_returns).cumprod()
    for name in growth:
        ax.plot(growth[name], lw=2, label=name,
                color=STRATEGY_COLOURS.get(name))
    spy = (1 + market.loc[growth.index]).cumprod()
    ax.plot(spy, color=SECTOR_COLOURS["Benchmark"], lw=2, ls="--",
            label=BENCHMARK)
    ax.axhline(1, color="black", lw=0.8)
    ax.set(title=title, ylabel="Value of $1")
    ax.legend(frameon=True, framealpha=0.9, loc="upper left")
    _save(fig, save_as)
    return fig

# ---------------------------------------------------------------- rolling-backtesting plot

def plot_weight_history(weight_history, save_as=None):
    """Max-Sharpe weights at each rebalance, summed by sector."""
    by_sector = weight_history.T.groupby(TICKER_SECTOR).sum().T[list(SECTORS)]
    # Repeat the last row one quarter later so the final holding period shows
    by_sector.loc[by_sector.index[-1] + pd.DateOffset(months=3)] = by_sector.iloc[-1]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.stackplot(by_sector.index, by_sector.T.values, step="post",
                 labels=by_sector.columns,
                 colors=[SECTOR_COLOURS[s] for s in by_sector.columns])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set(title="Max-Sharpe portfolio by sector at each quarterly rebalance",
           ylabel="Share of portfolio")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), frameon=False)
    _save(fig, save_as)
    return fig

# ---------------------------------------------------------------- sensitivity heatmap

def plot_commodity_betas(betas, tstats, labels, save_as=None):
    """Heatmap of commodity betas; * marks |t| > 2 (roughly 95% confidence)."""
    order = [t for group in SECTORS.values() for t in group if t in betas.index]
    cols = list(labels)
    shown = betas.loc[order, cols]
    stars = (tstats.loc[order, cols].abs() > 2).map(lambda sig: "*" if sig else "")
    text = shown.map(lambda v: f"{v:.2f}") + stars

    fig, ax = plt.subplots(figsize=(7, 8))
    limit = shown.abs().max().max()
    sns.heatmap(shown, annot=text, fmt="", cmap="RdBu_r", vmin=-limit,
                vmax=limit, cbar_kws={"label": "Beta (weekly)"}, ax=ax)
    ax.set_xticklabels([labels[c] for c in cols], rotation=20, ha="right")
    edge = 0
    for group in SECTORS.values():
        edge += len([t for t in group if t in shown.index])
        ax.axhline(edge, color="white", lw=3)
    ax.set_title("Sensitivity to commodity prices, controlling for the market")
    _save(fig, save_as)
    return fig

# ---------------------------------------------------------------- rolling-sensitivity

def plot_rolling_sector_beta(rolling, factor, label, save_as=None):
    """Sector-average rolling beta to one commodity over time."""
    one_factor = rolling.xs(factor, axis=1, level=1)
    by_sector = one_factor.T.groupby(TICKER_SECTOR).mean().T
    fig, ax = plt.subplots(figsize=(11, 5))
    for sector in SECTORS:
        ax.plot(by_sector[sector], lw=2, color=SECTOR_COLOURS[sector],
                label=sector)
    ax.axhline(0, color="black", lw=0.8)
    ax.axvspan(pd.Timestamp("2022-02-24"), pd.Timestamp("2022-12-31"),
               color="grey", alpha=0.15, label="2022 energy crisis")
    ax.set(title=f"Rolling 52-week beta to {label}, sector average",
           ylabel="Beta")
    ax.legend(frameon=False, loc="upper right")
    _save(fig, save_as)
    return fig