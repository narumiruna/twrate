import re

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from twrate.types import Exchange
from twrate.types import Rate

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_TIMEOUT = 30


def _extract_currency_code(cell: Tag) -> str | None:
    text = cell.get_text(separator=" ", strip=True).upper()
    match = re.search(r"[A-Z]{3}", text)
    return match.group(0) if match else None


def parse_line_rate_table(html: str) -> list[Rate]:
    soup = BeautifulSoup(html, "html.parser")

    rates: list[Rate] = []
    for row in soup.select("tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        source = _extract_currency_code(cells[0])
        if source is None:
            continue

        rate = Rate.model_validate(
            {
                "exchange": Exchange.LINE,
                "source": source,
                "target": "TWD",
                "spot_buy": cells[1].get_text(separator=" ", strip=True),
                "spot_sell": cells[2].get_text(separator=" ", strip=True),
            }
        )
        if rate.spot_buy is None and rate.spot_sell is None:
            continue

        rates.append(rate)

    if not rates:
        raise ValueError("No LINE Bank rates parsed from page")

    return rates


async def fetch_line_rates() -> list[Rate]:
    url = "https://www.linebank.com.tw/board-rate/exchange-rate"

    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()
        return parse_line_rate_table(resp.text)
