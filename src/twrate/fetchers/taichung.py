from typing import Any

import httpx

from ..types import Exchange
from ..types import Rate
from ._parsing import has_any_rate
from ._parsing import normalize_currency_code
from ._parsing import optional_mapping
from ._parsing import require_mapping

_TIMEOUT = 30
_API_URL = "https://openbank.tcbbank.com.tw/openAPI/v1.0.0/otherService/exchangeRates"
_CURRENCIES = (
    "USD",
    "EUR",
    "JPY",
    "CHF",
    "SGD",
    "CAD",
    "GBP",
    "NZD",
    "CNY",
    "HKD",
    "ZAR",
    "AUD",
    "SEK",
)


def _parse_rate(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def fetch_taichung_rates() -> list[Rate]:
    """Query Taichung Bank spot/cash rates via open banking endpoint."""
    params = {"currency": ",".join(_CURRENCIES)}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(_API_URL, params=params)
        resp.raise_for_status()

        payload = resp.json()

    payload = require_mapping(payload, "Unexpected Taichung Bank response format")
    rates_body = require_mapping(payload.get("appRepBody"), "Unexpected Taichung Bank response format")
    rates_data = rates_body.get("exchangeRates")
    if not isinstance(rates_data, list):
        raise ValueError("Unexpected Taichung Bank response format")

    rates: list[Rate] = []
    for item in rates_data:
        if not isinstance(item, dict):
            continue

        source = normalize_currency_code(item.get("currency"))
        if source is None:
            continue

        spot = optional_mapping(item.get("spotExchangeRate"))
        cash = optional_mapping(item.get("cashExchangeRate"))

        rate = Rate(
            exchange=Exchange.TAICHUNG,
            source=source,
            target="TWD",
            spot_buy=_parse_rate(spot.get("buy")),
            spot_sell=_parse_rate(spot.get("sale")),
            cash_buy=_parse_rate(cash.get("buy")),
            cash_sell=_parse_rate(cash.get("sale")),
        )

        if not has_any_rate(rate):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No Taichung Bank rates parsed from API response")

    return rates
