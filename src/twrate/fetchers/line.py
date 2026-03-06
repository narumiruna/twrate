import httpx
from bs4 import BeautifulSoup

from twrate.types import Exchange
from twrate.types import Rate

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_TIMEOUT = 30


async def fetch_line_rates() -> list[Rate]:
    url = "https://www.linebank.com.tw/board-rate/exchange-rate"

    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        tags = soup.select("tbody tr td")

        source = tags[0].get_text(separator=" ", strip=True).split(" ")[1].upper()
        spot_buy = float(tags[1].get_text(separator=" ", strip=True))
        spot_sell = float(tags[2].get_text(separator=" ", strip=True))

        return [
            Rate(
                exchange=Exchange.LINE,
                source=source,
                target="TWD",
                spot_buy=spot_buy,
                spot_sell=spot_sell,
            )
        ]
