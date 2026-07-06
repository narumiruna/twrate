from typing import Any
from typing import cast

import pytest
from pydantic import ValidationError

from twrate.fetchers.bot import _parse_bot_text
from twrate.fetchers.cooperative import _parse_rate as parse_cooperative_rate
from twrate.fetchers.dbs import RecDatum
from twrate.fetchers.esun import EsunRate
from twrate.fetchers.esun import _split_currency_pair
from twrate.fetchers.fubon import _parse_rate as parse_fubon_rate
from twrate.fetchers.line import parse_line_rate_table
from twrate.fetchers.megabank import _parse_rate as parse_megabank_rate
from twrate.fetchers.nextbank import parse_nextbank_payload
from twrate.fetchers.nextbank import parse_rate as parse_nextbank_rate
from twrate.fetchers.sinopac import SubInfoItem
from twrate.fetchers.sinopac import _build_sinopac_rate
from twrate.fetchers.sinopac import fetch_sinopac_rates
from twrate.fetchers.taichung import _parse_rate as parse_taichung_rate


def test_bot_parser_rejects_empty_response_with_value_error() -> None:
    with pytest.raises(ValueError, match="empty"):
        _parse_bot_text("")


def test_bot_parser_rejects_short_rows_with_value_error() -> None:
    header = " ".join(
        [
            "幣別",
            "placeholder",
            "現金",
            "即期",
            "c04",
            "c05",
            "c06",
            "c07",
            "c08",
            "c09",
            "c10",
            "c11",
            "現金",
            "即期",
        ]
    )

    with pytest.raises(ValueError, match="Unexpected row"):
        _parse_bot_text(f"{header}\nUSD 本行買入 31.0")


@pytest.mark.parametrize("ccy", ["", "USDTWD", "USD/TWD/EXTRA", "US Dollar/TWD", "USD/台幣"])
def test_esun_currency_pair_parser_rejects_malformed_pairs(ccy: str) -> None:
    assert _split_currency_pair(ccy) is None


def test_esun_currency_pair_parser_normalizes_valid_pairs() -> None:
    assert _split_currency_pair(" usd / twd ") == ("USD", "TWD")


def test_esun_rate_model_treats_missing_spot_rates_as_none() -> None:
    rate = EsunRate.model_validate(
        {
            "Name": "美元",
            "BBoardRate": "-",
            "SBoardRate": "",
            "CashBBoardRate": "31.0",
            "CashSBoardRate": "31.5",
            "BuyIncreaseRate": "-",
            "SellDecreaseRate": "-",
            "UpdateTime": "/Date(1747481401000)/",
            "CCY": "USD/TWD",
            "Key": "美元",
            "Url": None,
            "Title": None,
            "Serial": 0,
            "Alt": None,
            "Bonus": "",
            "CashBonus": None,
            "Description": None,
        }
    )

    assert rate.b_board_rate is None
    assert rate.s_board_rate is None
    assert rate.cash_b_board_rate == 31.0
    assert rate.cash_s_board_rate == 31.5


@pytest.mark.parametrize(
    "parse_rate",
    [parse_cooperative_rate, parse_fubon_rate, parse_megabank_rate, parse_nextbank_rate, parse_taichung_rate],
)
def test_json_rate_parsers_accept_numeric_values(parse_rate) -> None:
    assert parse_rate(cast(Any, 31.25)) == 31.25


@pytest.mark.parametrize(
    "parse_rate",
    [parse_cooperative_rate, parse_fubon_rate, parse_megabank_rate, parse_nextbank_rate, parse_taichung_rate],
)
def test_json_rate_parsers_reject_boolean_and_malformed_values(parse_rate) -> None:
    assert parse_rate(cast(Any, True)) is None
    assert parse_rate(cast(Any, [])) is None


def test_nextbank_parser_rejects_boolean_rate_values() -> None:
    payload = {"data": {"currencyList": [{"currency": "USD", "buyRate": True, "sellRate": False}]}}

    with pytest.raises(ValueError, match="No valid Next Bank rates"):
        parse_nextbank_payload(payload)


def test_dbs_rate_model_rejects_boolean_rate_values() -> None:
    with pytest.raises(ValidationError):
        RecDatum.model_validate(
            {"currency": "USD", "ttSell": True, "ttBuy": "31.0", "cashSell": None, "cashBuy": None}
        )


def test_esun_rate_model_rejects_boolean_rate_values() -> None:
    payload = {
        "Name": "美元",
        "BBoardRate": True,
        "SBoardRate": "31.5",
        "CashBBoardRate": "31.0",
        "CashSBoardRate": "31.5",
        "BuyIncreaseRate": "-",
        "SellDecreaseRate": "-",
        "UpdateTime": "/Date(1747481401000)/",
        "CCY": "USD/TWD",
        "Key": "美元",
        "Url": None,
        "Title": None,
        "Serial": 0,
        "Alt": None,
        "Bonus": "",
        "CashBonus": None,
        "Description": None,
    }

    with pytest.raises(ValidationError):
        EsunRate.model_validate(payload)


def test_sinopac_model_rejects_boolean_rate_values() -> None:
    with pytest.raises(ValidationError):
        SubInfoItem.model_validate(
            {
                "DataValue1": "美元(USD)",
                "DataValue1Img": "/USD.png",
                "DataValue2": True,
                "DataValue3": "31.5",
                "DataValue4": "USD",
            }
        )


def test_sinopac_build_rate_validates_values_before_assignment() -> None:
    item = SubInfoItem.model_validate(
        {
            "DataValue1": "美元(USD)",
            "DataValue1Img": "/USD.png",
            "DataValue2": "nan",
            "DataValue3": "31.5",
            "DataValue4": "USD",
        }
    )

    with pytest.raises(ValidationError):
        _build_sinopac_rate(item, "remit")


def test_line_parser_rejects_pages_without_rate_cells() -> None:
    with pytest.raises(ValueError, match="No LINE Bank rates"):
        parse_line_rate_table("<html><body>No table yet</body></html>")


def test_line_parser_extracts_currency_code_from_whitespace_separated_cell() -> None:
    html = """
    <table>
      <tbody>
        <tr>
          <td>美金 USD</td>
          <td>31.100</td>
          <td>31.300</td>
        </tr>
      </tbody>
    </table>
    """

    rates = parse_line_rate_table(html)

    assert len(rates) == 1
    assert rates[0].source == "USD"
    assert rates[0].spot_buy == 31.1
    assert rates[0].spot_sell == 31.3


@pytest.mark.asyncio
async def test_sinopac_rejects_invalid_exchange_type_before_request(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("network client should not be created for invalid exchange_type")

    monkeypatch.setattr("twrate.fetchers.sinopac.httpx.AsyncClient", FailingClient)

    with pytest.raises(ValueError, match="Invalid exchange type"):
        await fetch_sinopac_rates(cast(Any, "deposit"))


def test_nextbank_parser_skips_malformed_rows_and_normalizes_currency_codes() -> None:
    payload = {
        "data": {
            "currencyList": [
                [],
                {"currency": "US Dollar", "buyRate": "31.300", "sellRate": "31.100"},
                {"currency": " usd ", "buyRate": "31.300", "sellRate": "31.100"},
            ]
        }
    }

    rates = parse_nextbank_payload(payload)

    assert len(rates) == 1
    assert rates[0].source == "USD"
    assert rates[0].spot_buy == 31.1
    assert rates[0].spot_sell == 31.3
