import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def _parse_rate(value: str | None) -> float | None:
    """Parse a numeric rate value, treating missing values as ``None``."""
    if value is None:
        return None

    value = value.strip()
    if not value or value in {"-", "--"}:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def _extract_currency_code(value: str) -> str | None:
    normalized = re.sub(r"\s+", "", value)
    match = re.search(r"\(([A-Z]{3})\)", normalized)
    return match.group(1) if match else None


async def fetch_landbank_rates() -> list[Rate]:
    """Query Land Bank exchange rates."""
    url = "https://rate.landbank.com.tw/zh-TW/Foreign?mid=35"

    async with httpx.AsyncClient(
        verify=create_bank_ssl_context(),
        follow_redirects=True,
        timeout=_TIMEOUT,
    ) as client:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise ValueError("No exchange table found on Land Bank page")

    rates: list[Rate] = []
    for row in table.find_all("tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) < 5:
            continue

        source = _extract_currency_code(cols[0])
        if not source:
            continue

        spot_buy = _parse_rate(cols[1])
        spot_sell = _parse_rate(cols[2])
        cash_buy = _parse_rate(cols[3])
        cash_sell = _parse_rate(cols[4])

        if all(value is None for value in (spot_buy, spot_sell, cash_buy, cash_sell)):
            continue

        rates.append(
            Rate(
                exchange=Exchange.LANDBANK,
                source=source,
                target="TWD",
                spot_buy=spot_buy,
                spot_sell=spot_sell,
                cash_buy=cash_buy,
                cash_sell=cash_sell,
            )
        )

    if not rates:
        raise ValueError("No Land Bank rates parsed from page")

    return rates
