import httpx

from ..types import Exchange
from ..types import Rate
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30
_URL = "https://www.fubon.com/Fubon_Portal/banking/Personal/deposit/exchange_rate/exchange_rate1_newVersion.jsp"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def _parse_rate(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        return float(value.strip())
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

    rates_data = payload.get("FE_data")
    if not isinstance(rates_data, list):
        raise ValueError("Unexpected Fubon response format")

    rates: list[Rate] = []
    for item in rates_data:
        source = item.get("currencyEname")
        if not isinstance(source, str):
            continue

        source = source.strip().upper()
        if not source:
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

        if all(value is None for value in (rate.spot_buy, rate.spot_sell, rate.cash_buy, rate.cash_sell)):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No Fubon rates parsed from API response")

    return rates
