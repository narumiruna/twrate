import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate


def parse_rate(value: str) -> float | None:
    """Parse rate value, handling '--' or empty strings."""
    if not value or value == "--" or value == "-":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_currency_code(section) -> str | None:
    """Extract currency code from a section."""
    currency_name_div = section.find("div", class_="cubre-m-currency__name")
    if not currency_name_div:
        return None

    currency_text = currency_name_div.get_text(strip=True)
    # Format is like "美元USD" or "歐元EUR"
    match = re.search(r"([A-Z]{3})", currency_text)
    return match.group(1) if match else None


def parse_rate_table(table) -> tuple[float | None, float | None, float | None, float | None]:
    """Parse rate table and return (spot_buy, spot_sell, cash_buy, cash_sell)."""
    tbody = table.find("tbody")
    if not tbody:
        return None, None, None, None

    rows = tbody.find_all("tr")
    if len(rows) < 2:
        return None, None, None, None

    spot_buy = None
    spot_sell = None
    cash_buy = None
    cash_sell = None

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) < 3:
            continue

        row_type = cols[0]
        buy_rate = parse_rate(cols[1])
        sell_rate = parse_rate(cols[2])

        if "即期匯率" in row_type:
            spot_buy = buy_rate
            spot_sell = sell_rate
        elif "現鈔匯率" in row_type:
            cash_buy = buy_rate
            cash_sell = sell_rate

    return spot_buy, spot_sell, cash_buy, cash_sell


def parse_currency_section(section) -> Rate | None:
    """Parse a single currency section and return a Rate object."""
    currency_code = extract_currency_code(section)
    if not currency_code:
        return None

    table = section.find("table")
    if not table:
        return None

    spot_buy, spot_sell, cash_buy, cash_sell = parse_rate_table(table)

    return Rate(
        exchange=Exchange.CATHAY,
        source=currency_code,
        target="TWD",
        spot_buy=spot_buy,
        spot_sell=spot_sell,
        cash_buy=cash_buy,
        cash_sell=cash_sell,
    )


def fetch_cathay_rates() -> list[Rate]:
    """Query Cathay United Bank exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://www.cathaybk.com.tw/cathaybk/personal/product/deposit/currency-billboard/"

    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find all currency sections
    currency_sections = soup.find_all("div", class_="cubre-o-table__item")
    currency_sections = [
        s for s in currency_sections if isinstance(classes := s.get("class"), list) and "currency" in classes
    ]

    if not currency_sections:
        raise ValueError("No currency sections found in the Cathay United Bank page")

    rates = []
    for section in currency_sections:
        rate = parse_currency_section(section)
        if rate:
            rates.append(rate)

    return rates
