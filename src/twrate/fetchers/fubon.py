from typing import Any

import httpx

from ..types import Exchange
from ..types import Rate
from ._parsing import has_any_rate
from ._parsing import normalize_currency_code
from ._parsing import require_mapping
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30
_URL = "https://www.fubon.com/Fubon_Portal/banking/Personal/deposit/exchange_rate/exchange_rate1_newVersion.jsp"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def _parse_rate(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value or value == "-":
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def fetch_fubon_rates() -> list[Rate]:
    """Query Fubon Bank exchange rates."""
    async with httpx.AsyncClient(
        verify=create_bank_ssl_context(),
        follow_redirects=True,
        timeout=_TIMEOUT,
    ) as client:
        resp = await client.get(_URL, headers=_HEADERS)
        resp.raise_for_status()

        payload = resp.json()

    payload = require_mapping(payload, "Unexpected Fubon response format")
    rates_data = payload.get("FE_data")
    if not isinstance(rates_data, list):
        raise ValueError("Unexpected Fubon response format")

    rates: list[Rate] = []
    for item in rates_data:
        if not isinstance(item, dict):
            continue

        source = normalize_currency_code(item.get("currencyEname"))
        if source is None:
            continue

        rate = Rate(
            exchange=Exchange.FUBON,
            source=source,
            target="TWD",
            spot_buy=_parse_rate(item.get("Spot_BUY")),
            spot_sell=_parse_rate(item.get("Spot_SELL")),
            cash_buy=_parse_rate(item.get("cash_BUY")),
            cash_sell=_parse_rate(item.get("cash_SELL")),
        )

        if not has_any_rate(rate):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No Fubon rates parsed from API response")

    return rates
