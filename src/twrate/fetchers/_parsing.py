from collections.abc import Mapping
from typing import Any

from ..types import Rate
from ..types import _normalize_currency_code

normalize_currency_code = _normalize_currency_code


def parse_optional_rate(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def has_any_rate(rate: Rate) -> bool:
    return any(value is not None for value in (rate.spot_buy, rate.spot_sell, rate.cash_buy, rate.cash_sell))


def require_mapping(value: Any, message: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(message)
    return value


def optional_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}
