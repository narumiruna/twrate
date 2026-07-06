import math

import pytest
from pydantic import ValidationError

from twrate.types import Exchange
from twrate.types import Rate


def test_rate_normalizes_currency_codes_and_common_missing_rate_values() -> None:
    rate = Rate.model_validate(
        {
            "exchange": Exchange.BOT,
            "source": " usd ",
            "target": " twd ",
            "spot_buy": "1,234.50",
            "spot_sell": "0",
            "cash_buy": "-",
            "cash_sell": "",
        }
    )

    assert rate.source == "USD"
    assert rate.target == "TWD"
    assert rate.spot_buy == 1234.5
    assert rate.spot_sell is None
    assert rate.cash_buy is None
    assert rate.cash_sell is None


@pytest.mark.parametrize("source", ["", "US", "US Dollar", "US1", 123])
def test_rate_rejects_invalid_currency_code(source: object) -> None:
    with pytest.raises(ValidationError, match="currency code"):
        Rate.model_validate({"exchange": Exchange.BOT, "source": source, "target": "TWD", "spot_buy": "1.0"})


@pytest.mark.parametrize("value", ["-1", "nan", "inf", math.nan, math.inf, True])
def test_rate_rejects_negative_non_finite_and_bool_rates(value: object) -> None:
    with pytest.raises(ValidationError):
        Rate.model_validate({"exchange": Exchange.BOT, "source": "USD", "target": "TWD", "spot_buy": value})


def test_rate_validates_assignment_to_prevent_invalid_runtime_state() -> None:
    rate = Rate(exchange=Exchange.BOT, source="USD", target="TWD", spot_buy=1.0, spot_sell=1.0)

    with pytest.raises(ValidationError):
        rate.spot_buy = math.nan

    with pytest.raises(ValidationError):
        rate.spot_buy = -1.0

    assert rate.spot_buy == 1.0
