"""Project settings: which stocks, which dates, which assumptions."""

from pathlib import Path

# Folders (built relative to this file, so it works wherever you run from)
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

# Stocks grouped by sub-sector. All are US-listed, so every price is in USD.
SECTORS = {
    "Oil & Gas": ["XOM", "CVX", "SHEL", "BP", "TTE"],
    "Utilities": ["NEE", "DUK", "SO", "NGG"],
    "Renewables": ["FSLR", "ENPH", "BEP"],
}
BENCHMARK = "SPY"  # S&P 500 ETF, used as "the market"

# Flat list of every ticker, plus a lookup from ticker -> sector
TICKERS = [t for group in SECTORS.values() for t in group]
TICKER_SECTOR = {t: s for s, group in SECTORS.items() for t in group}

START_DATE = "2021-01-01"
END_DATE = "2026-01-01"  # five full calendar years

TRADING_DAYS = 252        # trading days in a year, used to annualise
RISK_FREE_RATE = 0.04     # 4% a year, roughly US T-bills over the period

# One colour per sector, used in every chart so they stay consistent
SECTOR_COLOURS = {
    "Oil & Gas": "#1f4e79",
    "Utilities": "#2e8b57",
    "Renewables": "#e69f00",
    "Benchmark": "#7f7f7f",
}