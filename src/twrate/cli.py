import typer
from rich import print
from tabulate import tabulate

from .bot import fetch_bot_rates
from .dbs import fetch_dbs_rates
from .esun import fetch_esun_rates
from .line import fetch_line_rates
from .sinopac import fetch_sinopac_rates
from .types import Rate


def run(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """

    rates = fetch_bot_rates() + fetch_dbs_rates() + fetch_sinopac_rates() + fetch_esun_rates() + fetch_line_rates()

    # filter rates by source_currency
    rates = [rate for rate in rates if rate.source == source_currency.upper()]

    # sort rates by spot_spread
    def sort_key(rate: Rate) -> float:
        if rate.spot_spread is None:
            return float("inf")
        return rate.spot_spread

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
