from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate
from ._parsing import has_any_rate
from ._parsing import normalize_currency_code
from ._parsing import require_mapping
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30
_PAGE_URL = "https://www.tcb-bank.com.tw/personal-banking/deposit-exchange/exchange-rate/spot"
_API_URL = "https://www.tcb-bank.com.tw/api/client/ForeignExchange/GetSpotForeignExchange"

_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
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


def _extract_token(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.select_one('form[data-form-id="spotrate"] input[name="__RequestVerificationToken"]')
    if token_input is None:
        raise ValueError("Could not find request verification token")

    value = token_input.get("value")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Invalid request verification token")

    return value


async def fetch_cooperative_bank_rates() -> list[Rate]:
    """Query Co-operative Bank (臺灣合作金庫) exchange rates."""
    async with httpx.AsyncClient(
        verify=create_bank_ssl_context(),
        follow_redirects=True,
        timeout=_TIMEOUT,
    ) as client:
        page_resp = await client.get(_PAGE_URL)
        page_resp.raise_for_status()

        token = _extract_token(page_resp.text)
        api_resp = await client.post(
            _API_URL,
            data={"__RequestVerificationToken": token},
            headers=_HEADERS,
        )
        api_resp.raise_for_status()

        payload = api_resp.json()

    payload = require_mapping(payload, "Unexpected Co-operative Bank API format")
    result = payload.get("result")
    if not isinstance(result, list):
        raise ValueError("Unexpected Co-operative Bank API format")

    by_currency: dict[str, dict[str, float | None]] = {}
    for item in result:
        if not isinstance(item, dict):
            continue

        source = normalize_currency_code(item.get("Currency"))
        if source is None:
            continue

        row = by_currency.setdefault(source, {"spot_buy": None, "spot_sell": None, "cash_buy": None, "cash_sell": None})

        match item.get("Type"):
            case "買入":
                row["spot_buy"] = _parse_rate(item.get("PromptExchange"))
                row["cash_buy"] = _parse_rate(item.get("CashExchange"))
            case "賣出":
                row["spot_sell"] = _parse_rate(item.get("PromptExchange"))
                row["cash_sell"] = _parse_rate(item.get("CashExchange"))

    rates: list[Rate] = []
    for source, row in by_currency.items():
        rate = Rate(
            exchange=Exchange.COOPERATIVE,
            source=source,
            target="TWD",
            spot_buy=row["spot_buy"],
            spot_sell=row["spot_sell"],
            cash_buy=row["cash_buy"],
            cash_sell=row["cash_sell"],
        )

        if not has_any_rate(rate):
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No Co-operative Bank rates parsed from API response")

    return rates
