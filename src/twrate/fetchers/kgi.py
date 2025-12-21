import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate


def _parse_rate(value: str) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fetch_kgi_rates() -> list[Rate]:
    """Query KGI Bank (凱基銀行) exchange rates by scraping the public page.

    Source: https://www.kgibank.com.tw/zh-tw/personal/interest-rate/fx
    """
    url = "https://www.kgibank.com.tw/zh-tw/personal/interest-rate/fx"
    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    rates: list[Rate] = []

    # Each desktop row contains a currency code span `.currency-en-name`
    # and four numeric cells under `.kgibOtherCus004__item-val span`:
    # [spot_buy, spot_sell, cash_buy, cash_sell]
    for row in soup.select(".kgibOtherCus004__item"):
        code_tag = row.select_one(".currency-en-name")
        if not code_tag:
            continue

        source = code_tag.get_text(strip=True).upper()

        # Collect numeric values from the row while skipping textual labels
        values: list[str] = []
        for span in row.select(".kgibOtherCus004__item-val span"):
            text = span.get_text(strip=True)
            # Accept only numbers (with optional decimal) or dash
            if re.fullmatch(r"-?|\d+(?:\.\d+)?", text):
                values.append(text)

        if len(values) < 4:
            # Mobile layout duplicates entries; still ensure we have four numbers
            continue

        spot_buy = _parse_rate(values[0])
        spot_sell = _parse_rate(values[1])
        cash_buy = _parse_rate(values[2])
        cash_sell = _parse_rate(values[3])

        rates.append(
            Rate(
                exchange=Exchange.KGI,
                source=source,
                target="TWD",
                spot_buy=spot_buy,
                spot_sell=spot_sell,
                cash_buy=cash_buy,
                cash_sell=cash_sell,
            )
        )

    if not rates:
        raise ValueError("No KGI rates parsed from page")

    return rates
