from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from twrate.fetcher import fetch_rates
from twrate.fetchers.line import fetch_line_rates
from twrate.types import Exchange

DATA_DIR = Path(__file__).parent / "data"

INTEGRATION_TEST_EXCHANGES = [e for e in Exchange if e != Exchange.LINE]


@pytest.mark.parametrize("exchange", INTEGRATION_TEST_EXCHANGES)
@pytest.mark.asyncio
async def test_fetch_rates(exchange: Exchange) -> None:
    rates = await fetch_rates(exchange)

    assert isinstance(rates, list)
    assert len(rates) > 0
    for rate in rates:
        assert rate.exchange == exchange
        assert rate.target == "TWD"
        assert rate.symbol == f"{rate.source}/{rate.target}"

        if rate.spot_buy is not None and rate.spot_sell is not None:
            assert rate.spot_buy > 0
            assert rate.spot_sell > 0
            assert rate.spot_mid == (rate.spot_buy + rate.spot_sell) / 2

        if rate.cash_buy is not None and rate.cash_sell is not None:
            assert rate.cash_buy > 0
            assert rate.cash_sell > 0
            assert rate.cash_mid == (rate.cash_buy + rate.cash_sell) / 2


@pytest.mark.asyncio
async def test_fetch_line_rates(httpx_mock: HTTPXMock) -> None:
    html = (DATA_DIR / "line.html").read_text()
    httpx_mock.add_response(url="https://www.linebank.com.tw/board-rate/exchange-rate", text=html)

    rates = await fetch_line_rates()

    assert isinstance(rates, list)
    assert len(rates) > 0
    for rate in rates:
        assert rate.exchange == Exchange.LINE
        assert rate.target == "TWD"
        assert rate.symbol == f"{rate.source}/{rate.target}"

        if rate.spot_buy is not None and rate.spot_sell is not None:
            assert rate.spot_buy > 0
            assert rate.spot_sell > 0
            assert rate.spot_mid == (rate.spot_buy + rate.spot_sell) / 2
