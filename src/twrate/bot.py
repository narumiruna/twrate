import httpx

from .types import Rate


# bank of taiwan
def query_bot_rates() -> list[Rate]:
    url = "https://rate.bot.com.tw/xrt/fltxt/0/day"

    resp = httpx.get(url)
    resp.raise_for_status()
    resp.encoding = "utf-8-sig"

    rates = []
    for i, row in enumerate(resp.text.splitlines()):
        if i == 0:
            cols = [s for s in row.split(" ") if s]
            assert cols[0] == "幣別"
            assert cols[2] == "現金"
            assert cols[3] == "即期"
            assert cols[12] == "現金"
            assert cols[13] == "即期"
        else:
            cols = [s for s in row.split(" ") if s]
            assert cols[1] == "本行買入"
            assert cols[11] == "本行賣出"

            rate = Rate(
                exchange="BOT",
                source=cols[0],
                target="TWD",
                spot_buy_rate=float(cols[3]),
                spot_sell_rate=float(cols[13]),
                cash_buy_rate=float(cols[2]),
                cash_sell_rate=float(cols[12]),
            )
            rates.append(rate)
    return rates
