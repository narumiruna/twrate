import json
import re

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from ..types import Exchange
from ..types import Rate
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30
_SCRIPT_URL = "https://www.taishinbank.com.tw/eServiceA/transactionrate/transactionrateExport.jsp?no=5"


def _decode_script_fragment(fragment: str) -> str:
    normalized = fragment.replace('\\"', '"').replace("\\'", "'").replace("\\/", "/")
    try:
        return json.loads(f'"{normalized}"')
    except json.JSONDecodeError:
        return normalized


def _parse_rate(value: str | None) -> float | None:
    if value is None:
        return None

    value = value.replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def _extract_currency(row: Tag) -> str | None:
    for anchor in row.find_all("a"):
        onclick = anchor.get("onclick")
        if not isinstance(onclick, str):
            continue

        match = re.search(r"queryhistory\('([A-Z]{3})'\)", onclick)
        if match:
            return match.group(1)

    return None


def _rate_columns_start(cells: list[Tag]) -> int:
    """Return the offset for rate columns.

    Some page variants prepend a currency label cell before rate values.
    """

    if len(cells) < 5:
        return 0

    first_rate = _parse_rate(cells[0].get_text(" ", strip=True))
    if first_rate is None:
        second_rate = _parse_rate(cells[1].get_text(" ", strip=True))
        if second_rate is not None:
            return 1

    return 0


def _extract_taishin_table_rates(table: Tag) -> list[Rate]:
    rows = table.find_all("tr")
    if not rows:
        return []

    header = "".join(cell.get_text("", strip=True) for cell in rows[0].find_all(["th", "td"]))
    if "即期買入" not in header or "現鈔賣出" not in header:
        return []

    rates: list[Rate] = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        source = _extract_currency(row)
        if not source:
            continue

        offset = _rate_columns_start(cells)
        if len(cells) < offset + 4:
            continue

        spot_buy = _parse_rate(cells[offset + 0].get_text(" ", strip=True))
        spot_sell = _parse_rate(cells[offset + 1].get_text(" ", strip=True))
        cash_buy = _parse_rate(cells[offset + 2].get_text(" ", strip=True))
        cash_sell = _parse_rate(cells[offset + 3].get_text(" ", strip=True))

        if all(value is None for value in (spot_buy, spot_sell, cash_buy, cash_sell)):
            continue

        rates.append(
            Rate(
                exchange=Exchange.TAISHIN,
                source=source,
                target="TWD",
                spot_buy=spot_buy,
                spot_sell=spot_sell,
                cash_buy=cash_buy,
                cash_sell=cash_sell,
            )
        )

    return rates


async def fetch_taishin_rates() -> list[Rate]:
    """Query Taishin Bank exchange rates."""
    async with httpx.AsyncClient(
        verify=create_bank_ssl_context(),
        follow_redirects=True,
        timeout=_TIMEOUT,
    ) as client:
        resp = await client.get(_SCRIPT_URL)
        resp.raise_for_status()

        fragments = re.findall(r"document\.writeln\((?:'|\")((?:.|\n)*?)(?:'|\")\);", resp.text)
        html = "".join(_decode_script_fragment(fragment) for fragment in fragments)

        soup = BeautifulSoup(html, "html.parser")

    rates = [rate for table in soup.find_all("table") for rate in _extract_taishin_table_rates(table)]
    if not rates:
        raise ValueError("No Taishin rates parsed from export script")

    return rates
