import sys

from app.repositories.klines_repository import KlinesRepository
from app.repositories.tickers_repository import TickersRepository


def main():
    """Run the scheduled ingestion jobs based on the CLI argument.

    Supported job types:
    - 'five-minutes': persist order book tickers.
    - 'hourly': persist 24-hour ticker summaries.
    - 'daily': persist klines for the 15m, 1h, and 1d timeframes.
    """
    repo_tickers = TickersRepository()
    repo_klines = KlinesRepository()
    job_type = sys.argv[1] if len(sys.argv) > 1 else "hourly"

    if job_type == "five-minutes":
        repo_tickers.save_orderbook_tickers()
    elif job_type == "hourly":
        repo_tickers.save_ticker_24hr()
    elif job_type == "daily":
        repo_klines.save_klines("15m")
        repo_klines.save_klines("1h")
        repo_klines.save_klines("1d")


if __name__ == "__main__":
    main()