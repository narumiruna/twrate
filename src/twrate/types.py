import math
import re
from datetime import datetime
from enum import StrEnum
from typing import Any

from loguru import logger
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

_CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")
_MISSING_RATE_VALUES = {"", "-", "--", "—", "N/A", "NA", "NULL"}


class Exchange(StrEnum):
    DBS = "DBS_BANK"
    SINOPAC = "BANK_SINOPAC"
    BOT = "BANK_OF_TAIWAN"
    ESUN = "ESUN_BANK"
    LINE = "LINE_BANK"
    HSBC = "HSBC_BANK"
    NEXT = "NEXT_BANK"
    KGI = "KGI_BANK"
    CATHAY = "CATHAY_BANK"
    MEGABANK = "MEGA_BANK"
    FIRSTBANK = "FIRST_BANK"
    LANDBANK = "LAND_BANK"
    YUANTA = "YUANTA_BANK"
    TAISHIN = "TAISHIN_BANK"
    TAICHUNG = "TAICHUNG_BANK"
    COOPERATIVE = "COOPERATIVE_BANK"
    FUBON = "FUBON_BANK"

    def __str__(self) -> str:
        return self.value


class Rate(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    exchange: Exchange
    source: str
    target: str
    spot_buy: float | None = None
    spot_sell: float | None = None
    cash_buy: float | None = None
    cash_sell: float | None = None
    fetched_at: datetime = Field(default_factory=datetime.now)

    @field_validator("source", "target", mode="before")
    @classmethod
    def normalize_currency_code(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("currency code must be a string")

        code = value.strip().upper()
        if not _CURRENCY_CODE_RE.fullmatch(code):
            raise ValueError("currency code must be a 3-letter currency code")

        return code

    @field_validator("spot_buy", "spot_sell", "cash_buy", "cash_sell", mode="before")
    @classmethod
    def parse_float(cls, value: Any) -> float | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise ValueError("rate value must be numeric, not boolean")

        if isinstance(value, int | float):
            number = float(value)
        elif isinstance(value, str):
            normalized = value.replace(",", "").strip()
            if normalized.upper() in _MISSING_RATE_VALUES:
                return None
            try:
                number = float(normalized)
            except ValueError as exc:
                raise ValueError(f"invalid rate value: {value!r}") from exc
        else:
            raise ValueError(f"invalid rate value type: {type(value).__name__}")

        if not math.isfinite(number):
            raise ValueError("rate value must be finite")

        if number < 0:
            raise ValueError("rate value must not be negative")

        if number == 0:
            return None

        return number

    @property
    def spot_mid(self) -> float | None:
        if self.spot_buy is None or self.spot_sell is None:
            logger.info("[{}:{}] spot_buy or spot_sell is None", self.exchange, self.symbol)
            return None
        return (self.spot_buy + self.spot_sell) / 2

    @property
    def cash_mid(self) -> float | None:
        if self.cash_buy is None or self.cash_sell is None:
            logger.info("[{}:{}] cash_buy or cash_sell is None", self.exchange, self.symbol)
            return None
        return (self.cash_buy + self.cash_sell) / 2

    @property
    def symbol(self) -> str:
        return f"{self.source}/{self.target}"

    @property
    def spot_spread(self) -> float | None:
        if self.spot_buy is None or self.spot_sell is None:
            logger.info("[{}:{}] spot_buy or spot_sell is None", self.exchange, self.symbol)
            return None

        mid = self.spot_mid
        if mid is None or not math.isfinite(mid) or mid <= 0:
            return None

        return (self.spot_sell - self.spot_buy) / mid

    @property
    def cash_spread(self) -> float | None:
        if self.cash_buy is None or self.cash_sell is None:
            logger.info("[{}:{}] cash_buy or cash_sell is None", self.exchange, self.symbol)
            return None

        mid = self.cash_mid
        if mid is None or not math.isfinite(mid) or mid <= 0:
            return None

        return (self.cash_sell - self.cash_buy) / mid
