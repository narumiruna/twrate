import pytest

from twrate.fetchers._parsing import has_any_rate
from twrate.fetchers._parsing import normalize_currency_code
from twrate.fetchers._parsing import optional_mapping
from twrate.fetchers._parsing import require_mapping
from twrate.types import Exchange
from twrate.types import Rate


@pytest.mark.parametrize(
    ("value", "expected"),
    [(" usd ", "USD"), ("CNH", "CNH"), ("US Dollar", None), ("US1", None), (None, None)],
)
def test_normalize_currency_code(value: object, expected: str | None) -> None:
    assert normalize_currency_code(value) == expected


def test_require_mapping_rejects_non_mapping_payloads() -> None:
    with pytest.raises(ValueError, match="bad payload"):
        require_mapping([], "bad payload")


def test_optional_mapping_turns_malformed_nested_objects_into_empty_mapping() -> None:
    assert optional_mapping(["not", "a", "mapping"]) == {}


def test_has_any_rate_detects_all_missing_rates() -> None:
    empty_rate = Rate(exchange=Exchange.LINE, source="USD", target="TWD")
    filled_rate = Rate(exchange=Exchange.LINE, source="USD", target="TWD", spot_buy=1.0)

    assert not has_any_rate(empty_rate)
    assert has_any_rate(filled_rate)
