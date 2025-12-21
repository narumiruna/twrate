import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate


def parse_rate(value: str) -> float | None:
    """Parse a rate value from string to float.

    Args:
        value: String representation of the rate

    Returns:
        Float value or None if parsing fails or value is empty/dash
    """
    if not value or value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fetch_nextbank_rates() -> list[Rate]:
    """Query Next Bank (將來銀行) Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://www.nextbank.com.tw/exchange-rates"

    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    rates = []
    table = soup.find("table")

    if not table:
        raise ValueError(
            "No exchange rates table found in the Next Bank page at https://www.nextbank.com.tw/exchange-rates"
        )

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("No tbody element found in the Next Bank exchange rates table")

    for row in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols or len(cols) < 5:
            continue

        # Extract currency code from the first column
        # Format is typically "Currency Name (CODE)" or just "CODE"
        currency_text = cols[0]
        # Try to match either "(CODE)" or standalone "CODE"
        match = re.search(r"\(([A-Z]{3})\)|\b([A-Z]{3})\b", currency_text)
        if not match:
            # Skip rows without valid currency codes
            continue
        currency_code = match.group(1) or match.group(2)

        rate = Rate(
            exchange=Exchange.NEXT,
            source=currency_code,
            target="TWD",
            spot_buy=parse_rate(cols[1]),
            spot_sell=parse_rate(cols[2]),
            cash_buy=parse_rate(cols[3]),
            cash_sell=parse_rate(cols[4]),
        )
        rates.append(rate)

    return rates
