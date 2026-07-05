import httpx

from ..types import Exchange
from ..types import Rate

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_TIMEOUT = 30


def check_header(header: str) -> None:
    columns = [s for s in header.split(" ") if s]
    if (
        columns[0] != "幣別"
        or columns[2] != "現金"
        or columns[3] != "即期"
        or columns[12] != "現金"
        or columns[13] != "即期"
    ):
        raise ValueError(f"Unexpected header value, got: {header}")


async def fetch_bot_rates() -> list[Rate]:
    """Query Bank of Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://rate.bot.com.tw/xrt/fltxt/0/day"

    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()
        resp.encoding = "utf-8-sig"

        # rate.bot.com.tw intermittently serves a JS anti-bot challenge page
        # instead of the plain-text rate table
        if resp.text.lstrip().lower().startswith(("<!doctype", "<html")):
            raise ValueError("rate.bot.com.tw returned an anti-bot challenge page instead of rate data")

        splits = resp.text.splitlines()
        header, rows = splits[0], splits[1:]
        check_header(header)

        rates = []
        for row in rows:
            columns = [s for s in row.split(" ") if s]

            if columns[1] != "本行買入" or columns[11] != "本行賣出":
                raise ValueError(f"Unexpected column value, got: {row}")

            rate = Rate(
                exchange=Exchange.BOT,
                source=columns[0],
                target="TWD",
                spot_buy=float(columns[3]),
                spot_sell=float(columns[13]),
                cash_buy=float(columns[2]),
                cash_sell=float(columns[12]),
            )
            rates.append(rate)
        return rates
