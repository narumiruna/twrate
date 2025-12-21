from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import typer
from loguru import logger
from rich import print
from tabulate import tabulate

from .fetcher import fetch_rates
from .types import Exchange
from .types import Rate


def run(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """

    rates: list[Rate] = []

    # Fetch rates in parallel
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_rates, exchange): exchange for exchange in Exchange}
        for future in as_completed(futures):
            exchange = futures[future]
            try:
                rates.extend(future.result())
            except Exception as e:
                logger.error(f"Error fetching {exchange.value}: {e}")

    # filter rates by source_currency
    rates = [rate for rate in rates if rate.source == source_currency.upper()]

    # sort rates by spot_spread
    def sort_key(rate: Rate) -> float:
        return rate.spot_spread or float("inf")

    rates = sorted(rates, key=sort_key)

    # build table
    table = [
        [
            rate.exchange,
            rate.spot_buy,
            rate.spot_sell,
            f"{rate.spot_spread * 100:.2f}%" if rate.spot_spread is not None else None,
            rate.cash_buy,
            rate.cash_sell,
            f"{rate.cash_spread * 100:.2f}%" if rate.cash_spread is not None else None,
        ]
        for rate in rates
    ]

    print(
        tabulate(
            table,
            headers=[
                "Exchange",
                "Spot Buy",
                "Spot Sell",
                "Spot Spread",
                "Cash Buy",
                "Cash Sell",
                "Cash Spread",
            ],
            stralign="right",
        )
    )


def main() -> None:
    typer.run(run)
