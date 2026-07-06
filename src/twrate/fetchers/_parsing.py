import re
from collections.abc import Mapping
from typing import Any

from ..types import Rate

_CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")


def normalize_currency_code(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    code = value.strip().upper()
    return code if _CURRENCY_CODE_RE.fullmatch(code) else None


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
