from curl_cffi.requests import AsyncSession

from ..types import Exchange
from ..types import Rate

# the endpoint serves the English table without an explicit locale
_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9",
}

_TIMEOUT = 30


def _split_columns(row: str) -> list[str]:
    return [s for s in row.split(" ") if s]


def check_header(header: str) -> None:
    columns = _split_columns(header)
    if len(columns) < 14:
        raise ValueError(f"Unexpected header value, got: {header}")

    if (
        columns[0] != "幣別"
        or columns[2] != "現金"
        or columns[3] != "即期"
        or columns[12] != "現金"
        or columns[13] != "即期"
    ):
        raise ValueError(f"Unexpected header value, got: {header}")


def _parse_bot_text(text: str) -> list[Rate]:
    if text.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError("rate.bot.com.tw returned an anti-bot challenge page instead of rate data")

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("BOT rate response is empty")

    header, rows = lines[0], lines[1:]
    check_header(header)

    rates: list[Rate] = []
    for row in rows:
        columns = _split_columns(row)
        if len(columns) < 14:
            raise ValueError(f"Unexpected row value, got: {row}")

        if columns[1] != "本行買入" or columns[11] != "本行賣出":
            raise ValueError(f"Unexpected column value, got: {row}")

        rates.append(
            Rate.model_validate(
                {
                    "exchange": Exchange.BOT,
                    "source": columns[0],
                    "target": "TWD",
                    "spot_buy": columns[3],
                    "spot_sell": columns[13],
                    "cash_buy": columns[2],
                    "cash_sell": columns[12],
                }
            )
        )

    if not rates:
        raise ValueError("No BOT rates parsed from response")

    return rates


async def fetch_bot_rates() -> list[Rate]:
    """Query Bank of Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://rate.bot.com.tw/xrt/fltxt/0/day"

    # rate.bot.com.tw serves a JS anti-bot challenge page to clients without a
    # browser TLS fingerprint, so impersonate one via curl_cffi
    async with AsyncSession(impersonate="chrome", timeout=_TIMEOUT) as session:
        resp = await session.get(url, headers=_HEADERS)
        resp.raise_for_status()

        text = resp.content.decode("utf-8-sig")
        return _parse_bot_text(text)
