from typing import Any

import httpx

from ..types import Exchange
from ..types import Rate
from ._parsing import has_any_rate
from ._parsing import normalize_currency_code
from ._parsing import optional_mapping
from ._parsing import require_mapping

_TIMEOUT = 30


def _parse_rate(value: Any) -> float | None:
    """Parse a numeric rate value, treating missing values as ``None``."""
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value or value in {"-", "--"}:
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def fetch_megabank_rates() -> list[Rate]:
    """Query Mega International Commercial Bank exchange rates."""
    url = "https://www.megabank.com.tw/api/client/ExchangeRate/GetRateData"
    params = {
        "sc_lang": "zh-TW",
        "sc_site": "bank-zh-tw",
        "dic_lang": "zh-TW",
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

        payload = require_mapping(resp.json(), "Unexpected response payload from Mega Bank")

        rates_data = payload.get("rates")
        if not isinstance(rates_data, list):
            raise ValueError("Unexpected response payload from Mega Bank")

        rates: list[Rate] = []
        for item in rates_data:
            if not isinstance(item, dict):
                continue

            curr_key = item.get("currKey", "")
            if not isinstance(curr_key, str):
                continue

            source = normalize_currency_code(curr_key.split("|")[0])
            if source is None:
                continue

            spot = optional_mapping(item.get("spot"))
            cash = optional_mapping(item.get("cash"))

            rate = Rate(
                exchange=Exchange.MEGABANK,
                source=source,
                target="TWD",
                spot_buy=_parse_rate(spot.get("bid")),
                spot_sell=_parse_rate(spot.get("ask")),
                cash_buy=_parse_rate(cash.get("bid")),
                cash_sell=_parse_rate(cash.get("ask")),
            )
            if not has_any_rate(rate):
                continue

            rates.append(rate)

        if not rates:
            raise ValueError("No Mega Bank rates parsed from API response")

        return rates
