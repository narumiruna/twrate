import typer
from rich import print
from tabulate import tabulate

from .bot import query_bot_rates
from .dbs import query_dbs_rates
from .esun import query_esun_rates
from .sinopac import query_sinopac_rates


def run(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """
    table = []

    rates = query_bot_rates() + query_dbs_rates() + query_sinopac_rates() + query_esun_rates()
    for rate in rates:
        if rate.source == source_currency.upper():
            table.append(
                [
                    rate.exchange,
                    rate.spot_buy,
                    rate.spot_sell,
                    rate.cash_buy,
                    rate.cash_sell,
                ]
            )
    print(tabulate(table, headers=["Exchange", "Spot Buy", "Spot Sell", "Cash Buy", "Cash Sell"]))


def main() -> None:
    typer.run(run)
