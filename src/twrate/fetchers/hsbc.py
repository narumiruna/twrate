import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate


def parse_rate(value: str) -> float | None:
    if not value or value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fetch_hsbc_rates() -> list[Rate]:
    """Query HSBC Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://www.hsbc.com.tw/currency-rates/"

    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    rates = []
    table = soup.find("table")

    if not table:
        raise ValueError("No table found in the HSBC currency rates page")

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("No tbody found in the HSBC currency rates table")

    for row in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols or len(cols) < 5:
            continue

        # Extract currency code from the first column
        # Format is typically "Currency Name (CODE)"
        currency_text = cols[0]
        match = re.search(r"\(([A-Z]{3})\)", currency_text)
        currency_code = match.group(1) if match else currency_text.strip()

        rate = Rate(
            exchange=Exchange.HSBC,
            source=currency_code,
            target="TWD",
            spot_buy=parse_rate(cols[1]),
            spot_sell=parse_rate(cols[2]),
            cash_buy=parse_rate(cols[3]),
            cash_sell=parse_rate(cols[4]),
        )
        rates.append(rate)

    return rates
