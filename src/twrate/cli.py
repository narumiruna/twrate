import asyncio

import typer
from loguru import logger
from rich import print
from tabulate import tabulate

from .fetcher import fetch_rates
from .types import Exchange
from .types import Rate


async def run_async(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """

    # Fetch all rates concurrently
    tasks = [fetch_rates(exchange) for exchange in Exchange]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    rates: list[Rate] = []
    for exchange, result in zip(Exchange, results, strict=False):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch rates from {exchange.name}: {result}")
        elif isinstance(result, list):
            rates.extend(result)

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


def run(source_currency: str) -> None:
    """Synchronous wrapper for run_async."""
    asyncio.run(run_async(source_currency))


def main() -> None:
    typer.run(run)
