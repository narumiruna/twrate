import httpx

from ..types import Exchange
from ..types import Rate


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


async def fetch_nextbank_rates() -> list[Rate]:
    """Query Next Bank (將來銀行) Taiwan exchange rates via public API."""

    api_url = "https://api.nextbank.com.tw/ap6/open/forex/v1.0/GetFXRate"

    async with httpx.AsyncClient() as client:
        resp = await client.post(api_url, json={}, follow_redirects=True)
        resp.raise_for_status()

        data = resp.json()
        currency_list = data.get("data", {}).get("currencyList")
        if not currency_list:
            raise ValueError(
                "No exchange rates returned from Next Bank API at https://api.nextbank.com.tw/ap6/open/forex/v1.0/GetFXRate"
            )

        rates: list[Rate] = []
        for item in currency_list:
            currency_code = item.get("currency")
            buy_rate = parse_rate(item.get("buyRate"))
            sell_rate = parse_rate(item.get("sellRate"))

            if not currency_code:
                continue

            # API returns buyRate as bank sells to customer, so swap to our Spot Buy/Sell semantics.
            rates.append(
                Rate(
                    exchange=Exchange.NEXT,
                    source=currency_code,
                    target="TWD",
                    spot_buy=sell_rate,
                    spot_sell=buy_rate,
                    cash_buy=None,
                    cash_sell=None,
                )
            )

        if not rates:
            raise ValueError("No valid Next Bank rates parsed from API response")

        return rates
