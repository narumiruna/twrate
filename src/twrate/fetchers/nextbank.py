import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate

# Mapping of Chinese currency names to ISO currency codes
CURRENCY_NAME_MAP = {
    "美元": "USD",
    "歐元": "EUR",
    "日圓": "JPY",
    "英鎊": "GBP",
    "澳幣": "AUD",
    "加拿大幣": "CAD",
    "加幣": "CAD",
    "新加坡幣": "SGD",
    "瑞士法郎": "CHF",
    "港幣": "HKD",
    "人民幣": "CNY",
    "南非幣": "ZAR",
    "瑞典幣": "SEK",
    "紐元": "NZD",
    "泰銖": "THB",
    "菲國比索": "PHP",
    "印尼幣": "IDR",
    "韓元": "KRW",
    "馬來幣": "MYR",
    "越南盾": "VND",
}


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


def extract_currency_code(text: str) -> str | None:
    """Extract ISO currency code from text.

    Args:
        text: Text containing currency name (Chinese or English)

    Returns:
        ISO currency code (e.g., 'USD') or None if not found
    """
    # First try to find Chinese currency name
    for cn_name, iso_code in CURRENCY_NAME_MAP.items():
        if cn_name in text:
            return iso_code

    # Fall back to extracting ISO code from text
    # Try to match either "(CODE)" or standalone "CODE"
    match = re.search(r"\(([A-Z]{3})\)|\b([A-Z]{3})\b", text)
    if match:
        return match.group(1) or match.group(2)

    return None


def find_currency_rows(soup: BeautifulSoup) -> list:
    """Find currency rows in the HTML.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of elements containing currency data
    """
    # Try to find currency rows in various possible structures
    possible_selectors = [
        "div.currency-row",
        "div[class*='currency']",
        "div[class*='exchange']",
        "li[class*='currency']",
        "li[class*='exchange']",
    ]

    for selector in possible_selectors:
        elements = soup.select(selector)
        if elements:
            return elements

    # If no specific currency divs found, try to find any divs containing Chinese currency names
    currency_rows = []
    all_divs = soup.find_all("div")
    for div in all_divs:
        text = div.get_text(strip=True)
        # Check if this div contains a currency name and has rate-like numbers
        if any(cn_name in text for cn_name in CURRENCY_NAME_MAP) and re.search(r"\d+\.\d{2,}", text):
            currency_rows.append(div)

    return currency_rows


def parse_currency_row(row) -> Rate | None:
    """Parse a single currency row into a Rate object.

    Args:
        row: HTML element containing currency data

    Returns:
        Rate object or None if parsing fails
    """
    text = row.get_text(separator=" ", strip=True)

    # Extract currency code
    currency_code = extract_currency_code(text)
    if not currency_code:
        return None

    # Extract all numbers that look like rates (format: XX.XXXX or similar)
    rate_numbers = re.findall(r"\d+\.\d{2,}", text)

    # Next Bank typically shows: [spot_buy, spot_sell, cash_buy, cash_sell]
    # Or sometimes just [spot_buy, spot_sell]
    if len(rate_numbers) < 2:
        return None

    spot_buy = parse_rate(rate_numbers[0])
    spot_sell = parse_rate(rate_numbers[1])
    cash_buy = parse_rate(rate_numbers[2]) if len(rate_numbers) > 2 else None
    cash_sell = parse_rate(rate_numbers[3]) if len(rate_numbers) > 3 else None

    return Rate(
        exchange=Exchange.NEXT,
        source=currency_code,
        target="TWD",
        spot_buy=spot_buy,
        spot_sell=spot_sell,
        cash_buy=cash_buy,
        cash_sell=cash_sell,
    )


def fetch_nextbank_rates() -> list[Rate]:
    """Query Next Bank (將來銀行) Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://www.nextbank.com.tw/exchange-rates"

    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find currency rows in the page
    currency_rows = find_currency_rows(soup)

    if not currency_rows:
        raise ValueError(
            "No exchange rate data found in the Next Bank page at https://www.nextbank.com.tw/exchange-rates"
        )

    # Parse each currency row
    rates = []
    for row in currency_rows:
        rate = parse_currency_row(row)
        if rate:
            rates.append(rate)

    return rates
