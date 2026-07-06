import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate
from ._parsing import normalize_currency_code

_TIMEOUT = 30


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
    return normalize_currency_code(match.group(1)) if match else None


async def fetch_firstbank_rates() -> list[Rate]:  # noqa: C901
    """Query First Bank exchange rates."""
    url = "https://www.firstbank.com.tw/sites/fcb/touch/1565688252532"

    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
        resp = await client.get(url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise ValueError("No exchange table found on First Bank page")

    rows = table.find_all("tr")
    if not rows:
        raise ValueError("No exchange rows found on First Bank page")

    values: dict[str, dict[str, float | None]] = {}
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) < 4:
            continue

        source = _extract_currency_code(cols[0])
        if not source:
            continue

        rate_type = cols[1]
        buy_rate = _parse_rate(cols[2])
        sell_rate = _parse_rate(cols[3])

        bucket = values.setdefault(source, {"spot_buy": None, "spot_sell": None, "cash_buy": None, "cash_sell": None})

        if "即期" in rate_type:
            bucket["spot_buy"] = buy_rate
            bucket["spot_sell"] = sell_rate
        elif "現鈔" in rate_type:
            bucket["cash_buy"] = buy_rate
            bucket["cash_sell"] = sell_rate

    if not values:
        raise ValueError("No First Bank rates parsed")

    rates: list[Rate] = []
    for source, raw in values.items():
        if all(value is None for value in raw.values()):
            continue

        rates.append(
            Rate(
                exchange=Exchange.FIRSTBANK,
                source=source,
                target="TWD",
                spot_buy=raw["spot_buy"],
                spot_sell=raw["spot_sell"],
                cash_buy=raw["cash_buy"],
                cash_sell=raw["cash_sell"],
            )
        )

    if not rates:
        raise ValueError("No First Bank rates with numeric values parsed")

    return rates
