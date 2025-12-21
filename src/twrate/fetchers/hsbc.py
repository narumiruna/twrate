from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate


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
        # Format is typically "Currency Name (CODE)" or just "CODE"
        currency_text = cols[0]
        if "(" in currency_text and ")" in currency_text:
            # Extract code from parentheses
            currency_code = currency_text.split("(")[1].split(")")[0].strip()
        else:
            # Use the text as-is if no parentheses
            currency_code = currency_text.strip()

        # Parse float values, handling '-' or empty strings
        def parse_rate(value: str) -> float | None:
            if not value or value == "-" or value == "":
                return None
            try:
                return float(value)
            except ValueError:
                return None

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
