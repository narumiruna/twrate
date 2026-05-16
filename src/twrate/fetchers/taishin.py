import json
import re

import httpx
from bs4 import BeautifulSoup

from ..types import Exchange
from ..types import Rate
from ._ssl import create_bank_ssl_context

_TIMEOUT = 30
_SCRIPT_URL = "https://www.taishinbank.com.tw/eServiceA/transactionrate/transactionrateExport.jsp?no=5"


def _decode_script_fragment(fragment: str) -> str:
    normalized = fragment.replace("\\\"", '"').replace("\\'", "'").replace('\\/', '/')
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


def _extract_currency(row: object) -> str | None:
    for anchor in row.find_all("a"):
        onclick = anchor.get("onclick", "")
        match = re.search(r"queryhistory\('([A-Z]{3})'\)", onclick)
        if match:
            return match.group(1)

    return None


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

    tables = soup.find_all("table")
    if not tables:
        raise ValueError("No exchange tables found in Taishin script output")

    rates: list[Rate] = []
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        header = "".join(cell.get_text("", strip=True) for cell in rows[0].find_all(["th", "td"]))
        if "即期買入" not in header or "現鈔賣出" not in header:
            continue

        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            source = _extract_currency(row)
            if not source:
                continue

            spot_buy = _parse_rate(cells[0].get_text(" ", strip=True))
            spot_sell = _parse_rate(cells[1].get_text(" ", strip=True))
            cash_buy = _parse_rate(cells[2].get_text(" ", strip=True))
            cash_sell = _parse_rate(cells[3].get_text(" ", strip=True))

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

    if not rates:
        raise ValueError("No Taishin rates parsed from export script")

    return rates
