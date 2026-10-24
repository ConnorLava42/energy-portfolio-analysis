"""Every chart in the project. Each function can save a PNG to figures/."""

import matplotlib.pyplot as plt
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