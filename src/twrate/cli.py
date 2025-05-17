import typer
from rich import print
from tabulate import tabulate

from .bot import query_bot_rates
from .dbs import query_dbs_rates
from .esun import query_esun_rates
from .sinopac import query_sinopac_rates
from .types import Rate


def run(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """
    table = []

    rates = query_bot_rates() + query_dbs_rates() + query_sinopac_rates() + query_esun_rates()

    # sort rates by spot_spread
    def sort_key(rate: Rate) -> float:
        if rate.spot_spread is None:
            return float("inf")
        return rate.spot_spread

    rates = sorted(rates, key=sort_key)

    for rate in rates:
        if rate.source == source_currency.upper():
            table.append(
                [
                    rate.exchange,
                    rate.spot_buy,
                    rate.spot_sell,
                    f"{rate.spot_spread * 100:.2f}%" if rate.spot_spread is not None else None,
                    rate.cash_buy,
                    rate.cash_sell,
                    f"{rate.cash_spread * 100:.2f}%" if rate.cash_spread is not None else None,
                ]
            )

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
