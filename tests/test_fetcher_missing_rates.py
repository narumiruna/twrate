from collections.abc import Awaitable
from collections.abc import Callable
from typing import Self

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from twrate.fetchers.firstbank import fetch_firstbank_rates
from twrate.fetchers.landbank import fetch_landbank_rates
from twrate.fetchers.line import parse_line_rate_table
from twrate.fetchers.taishin import _extract_taishin_table_rates
from twrate.fetchers.taishin import fetch_taishin_rates
from twrate.fetchers.yuanta import fetch_yuanta_rates
from twrate.types import Exchange
from twrate.types import Rate


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        pass


def _mock_html_client(monkeypatch: pytest.MonkeyPatch, path: str, html: str) -> None:
    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def get(self, *args: object, **kwargs: object) -> _FakeResponse:
            return _FakeResponse(html)

    monkeypatch.setattr(path, FakeAsyncClient)


_Fetcher = Callable[[], Awaitable[list[Rate]]]


@pytest.mark.parametrize(
    ("fetcher", "client_path", "exchange", "html"),
    [
        (
            fetch_firstbank_rates,
            "twrate.fetchers.firstbank.httpx.AsyncClient",
            Exchange.FIRSTBANK,
            """
            <table>
              <tr><td>美元 (USD)</td><td>即期</td><td>-</td><td>-</td></tr>
              <tr><td>歐元 (EUR)</td><td>即期</td><td>32.1</td><td>-</td></tr>
            </table>
            """,
        ),
        (
            fetch_landbank_rates,
            "twrate.fetchers.landbank.httpx.AsyncClient",
            Exchange.LANDBANK,
            """
            <table>
              <tr><td>美元 (USD)</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
              <tr><td>歐元 (EUR)</td><td>32.1</td><td>-</td><td>-</td><td>-</td></tr>
            </table>
            """,
        ),
        (
            fetch_yuanta_rates,
            "twrate.fetchers.yuanta.httpx.AsyncClient",
            Exchange.YUANTA,
            """
            <table>
              <tr><td>美元 (USD)</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
              <tr><td>歐元 (EUR)</td><td>32.1</td><td>-</td><td>-</td><td>-</td></tr>
            </table>
            """,
        ),
    ],
)
@pytest.mark.asyncio
async def test_html_fetchers_skip_empty_rates_and_keep_partial_rates(
    monkeypatch: pytest.MonkeyPatch,
    fetcher: _Fetcher,
    client_path: str,
    exchange: Exchange,
    html: str,
) -> None:
    _mock_html_client(monkeypatch, client_path, html)

    rates = await fetcher()

    assert len(rates) == 1
    assert rates[0].exchange == exchange
    assert rates[0].source == "EUR"
    assert rates[0].spot_buy == 32.1


@pytest.mark.parametrize(
    ("fetcher", "client_path", "html", "error"),
    [
        (
            fetch_firstbank_rates,
            "twrate.fetchers.firstbank.httpx.AsyncClient",
            "<table><tr><td>美元 (USD)</td><td>即期</td><td>-</td><td>-</td></tr></table>",
            "No First Bank rates with numeric values parsed",
        ),
        (
            fetch_landbank_rates,
            "twrate.fetchers.landbank.httpx.AsyncClient",
            "<table><tr><td>美元 (USD)</td><td>-</td><td>-</td><td>-</td><td>-</td></tr></table>",
            "No Land Bank rates parsed from page",
        ),
        (
            fetch_yuanta_rates,
            "twrate.fetchers.yuanta.httpx.AsyncClient",
            "<table><tr><td>美元 (USD)</td><td>-</td><td>-</td><td>-</td><td>-</td></tr></table>",
            "No Yuanta Bank rates parsed from page",
        ),
    ],
)
@pytest.mark.asyncio
async def test_html_fetchers_preserve_no_rates_errors(
    monkeypatch: pytest.MonkeyPatch,
    fetcher: _Fetcher,
    client_path: str,
    html: str,
    error: str,
) -> None:
    _mock_html_client(monkeypatch, client_path, html)

    with pytest.raises(ValueError, match=error):
        await fetcher()


def test_line_parser_skips_empty_rates_and_keeps_partial_rates() -> None:
    html = """
    <table><tbody>
      <tr><td>美元 USD</td><td>-</td><td>-</td></tr>
      <tr><td>歐元 EUR</td><td>32.1</td><td>-</td></tr>
    </tbody></table>
    """

    rates = parse_line_rate_table(html)

    assert len(rates) == 1
    assert rates[0].source == "EUR"
    assert rates[0].spot_buy == 32.1


def test_line_parser_preserves_no_rates_error() -> None:
    html = "<table><tbody><tr><td>美元 USD</td><td>-</td><td>-</td></tr></tbody></table>"

    with pytest.raises(ValueError, match="No LINE Bank rates parsed from page"):
        parse_line_rate_table(html)


def _taishin_table(html: str) -> Tag:
    table = BeautifulSoup(html, "html.parser").find("table")
    assert isinstance(table, Tag)
    return table


def test_taishin_parser_skips_empty_rates_and_keeps_partial_rates() -> None:
    table = _taishin_table(
        """
        <table>
          <tr><th>即期買入</th><th>即期賣出</th><th>現鈔買入</th><th>現鈔賣出</th></tr>
          <tr><td><a onclick="queryhistory('USD')">USD</a></td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
          <tr><td><a onclick="queryhistory('EUR')">EUR</a></td><td>32.1</td><td>-</td><td>-</td><td>-</td></tr>
        </table>
        """
    )

    rates = _extract_taishin_table_rates(table)

    assert len(rates) == 1
    assert rates[0].source == "EUR"
    assert rates[0].spot_buy == 32.1


def test_taishin_parser_returns_no_rates_for_empty_rows() -> None:
    table = _taishin_table(
        """
        <table>
          <tr><th>即期買入</th><th>即期賣出</th><th>現鈔買入</th><th>現鈔賣出</th></tr>
          <tr><td><a onclick="queryhistory('USD')">USD</a></td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
        </table>
        """
    )

    assert _extract_taishin_table_rates(table) == []


@pytest.mark.asyncio
async def test_taishin_fetcher_preserves_no_rates_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_html_client(
        monkeypatch,
        "twrate.fetchers.taishin.httpx.AsyncClient",
        "document.writeln('<table><tr></tr></table>');",
    )

    with pytest.raises(ValueError, match="No Taishin rates parsed from export script"):
        await fetch_taishin_rates()
