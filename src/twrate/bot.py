import httpx

from .types import Rate


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


def query_bot_rates() -> list[Rate]:
    """Query Bank of Taiwan exchange rates.

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    url = "https://rate.bot.com.tw/xrt/fltxt/0/day"

    resp = httpx.get(url)
    resp.raise_for_status()
    resp.encoding = "utf-8-sig"

    splits = resp.text.splitlines()
    header, rows = splits[0], splits[1:]
    check_header(header)

    rates = []
    for row in rows:
        columns = [s for s in row.split(" ") if s]

        if columns[1] != "本行買入" or columns[11] != "本行賣出":
            raise ValueError(f"Unexpected column value, got: {row}")

        rate = Rate(
            exchange="BOT",
            source=columns[0],
            target="TWD",
            spot_buy=float(columns[3]),
            spot_sell=float(columns[13]),
            cash_buy=float(columns[2]),
            cash_sell=float(columns[12]),
        )
        rates.append(rate)
    return rates
