import asyncio
from typing import cast

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from .fetcher import fetch_rates
from .types import Exchange
from .types import Rate

BANK_NAME_ZHTW = {
    Exchange.BOT: "台灣銀行",
    Exchange.DBS: "星展銀行",
    Exchange.SINOPAC: "永豐銀行",
    Exchange.ESUN: "玉山銀行",
    Exchange.LINE: "LINE Bank",
    Exchange.HSBC: "匯豐銀行",
    Exchange.NEXT: "將來銀行",
    Exchange.KGI: "凱基銀行",
    Exchange.CATHAY: "國泰世華銀行",
    Exchange.MEGABANK: "兆豐銀行",
    Exchange.FIRSTBANK: "第一銀行",
    Exchange.LANDBANK: "土地銀行",
    Exchange.YUANTA: "元大銀行",
    Exchange.TAISHIN: "台新銀行",
    Exchange.TAICHUNG: "台中銀行",
    Exchange.COOPERATIVE: "合作金庫",
    Exchange.FUBON: "台北富邦銀行",
}


def _exchange_display(exchange: Exchange) -> str:
    return BANK_NAME_ZHTW.get(exchange, exchange.value)


async def fetch_all_rates() -> list[Rate]:
    """Fetch rates from all exchanges in parallel using asyncio."""
    rates: list[Rate] = []

    # Create tasks for all exchanges
    tasks = [fetch_rates(exchange) for exchange in Exchange]

    # Gather results, handling exceptions
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for exchange, result in zip(Exchange, results, strict=False):
        if isinstance(result, Exception):
            logger.error("Error fetching {:12s}: {}", exchange.value, result)
        else:
            rates.extend(cast(list[Rate], result))

    return rates


def run(source_currency: str) -> None:
    """Query currency rates from various exchanges and display them in a table.

    Args:
        source_currency (str): The source currency to query rates for.
    """
    # Fetch rates using asyncio
    rates = asyncio.run(fetch_all_rates())

    # filter rates by source_currency
    rates = [rate for rate in rates if rate.source == source_currency.upper()]

    # sort rates by spot_spread
    def sort_key(rate: Rate) -> float:
        return rate.spot_spread or float("inf")

    rates = sorted(rates, key=sort_key)

    def _fmt_float(value: float | None) -> str:
        return f"{value:.4f}" if value is not None else "-"

    def _fmt_pct(value: float | None) -> str:
        return f"{value * 100:.2f}%" if value is not None else "-"

    table = Table(title=f"{source_currency.upper()} 各行即時牌價")
    table.add_column("銀行", justify="left")
    table.add_column("代號", justify="left")
    table.add_column("即期買進", justify="right")
    table.add_column("即期賣出", justify="right")
    table.add_column("即期點差", justify="right")
    table.add_column("現鈔買進", justify="right")
    table.add_column("現鈔賣出", justify="right")
    table.add_column("現鈔點差", justify="right")

    for rate in rates:
        table.add_row(
            _exchange_display(rate.exchange),
            rate.exchange.value,
            _fmt_float(rate.spot_buy),
            _fmt_float(rate.spot_sell),
            _fmt_pct(rate.spot_spread),
            _fmt_float(rate.cash_buy),
            _fmt_float(rate.cash_sell),
            _fmt_pct(rate.cash_spread),
        )

    Console().print(table)


def main() -> None:
    typer.run(run)
