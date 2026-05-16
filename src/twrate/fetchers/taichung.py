import httpx

from ..types import Exchange
from ..types import Rate

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


def _parse_rate(value: str | None) -> float | None:
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

    rates_body = payload.get("appRepBody", {})
    rates_data = rates_body.get("exchangeRates")
    if not isinstance(rates_data, list):
        raise ValueError("Unexpected Taichung Bank response format")

    rates: list[Rate] = []
    for item in rates_data:
        source = item.get("currency", "")
        if not isinstance(source, str):
            continue

        source = source.strip().upper()
        if not source:
            continue

        spot = item.get("spotExchangeRate") or {}
        cash = item.get("cashExchangeRate") or {}

        rate = Rate(
            exchange=Exchange.TAICHUNG,
            source=source,
            target="TWD",
            spot_buy=_parse_rate(spot.get("buy")),
            spot_sell=_parse_rate(spot.get("sale")),
            cash_buy=_parse_rate(cash.get("buy")),
            cash_sell=_parse_rate(cash.get("sale")),
        )

        if all(value is None for value in (rate.spot_buy, rate.spot_sell, rate.cash_buy, rate.cash_sell)):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No Taichung Bank rates parsed from API response")

    return rates
