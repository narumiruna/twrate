from typing import Any

import httpx

from ..types import Exchange
from ..types import Rate
from ._parsing import has_any_rate
from ._parsing import normalize_currency_code
from ._parsing import require_mapping
from ._ssl import create_bank_ssl_context


def parse_rate(value: Any) -> float | None:
    """Parse a rate value from string to float.

    Args:
        value: String representation of the rate

    Returns:
        Float value or None if parsing fails or value is empty/dash
    """
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


def parse_nextbank_payload(data: Any) -> list[Rate]:
    payload = require_mapping(data, "Unexpected Next Bank API format")

    data_body = require_mapping(
        payload.get("data"),
        "No exchange rates returned from Next Bank API at https://api.nextbank.com.tw/ap6/open/forex/v1.0/GetFXRate",
    )

    currency_list = data_body.get("currencyList")
    if not isinstance(currency_list, list) or not currency_list:
        raise ValueError(
            "No exchange rates returned from Next Bank API at https://api.nextbank.com.tw/ap6/open/forex/v1.0/GetFXRate"
        )

    rates: list[Rate] = []
    for item in currency_list:
        if not isinstance(item, dict):
            continue

        currency_code = normalize_currency_code(item.get("currency"))
        if currency_code is None:
            continue

        buy_rate = parse_rate(item.get("buyRate"))
        sell_rate = parse_rate(item.get("sellRate"))

        rate = Rate(
            exchange=Exchange.NEXT,
            source=currency_code,
            target="TWD",
            # API returns buyRate as bank sells to customer, so swap to our Spot Buy/Sell semantics.
            spot_buy=sell_rate,
            spot_sell=buy_rate,
            cash_buy=None,
            cash_sell=None,
        )
        if not has_any_rate(rate):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No valid Next Bank rates parsed from API response")

    return rates


async def fetch_nextbank_rates() -> list[Rate]:
    """Query Next Bank (將來銀行) Taiwan exchange rates via public API."""

    api_url = "https://api.nextbank.com.tw/ap6/open/forex/v1.0/GetFXRate"

    async with httpx.AsyncClient(verify=create_bank_ssl_context()) as client:
        resp = await client.post(api_url, json={}, follow_redirects=True)
        resp.raise_for_status()

        return parse_nextbank_payload(resp.json())
