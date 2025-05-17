from enum import Enum

from loguru import logger
from pydantic import BaseModel
from pydantic import field_validator


class Exchange(str, Enum):
    DBS = "DBS"
    SINOPAC = "SINOPAC"
    BOT = "BANK_OF_TAIWAN"
    ESUN = "ESUN"

    def __str__(self) -> str:
        return self.value


class Rate(BaseModel):
    exchange: Exchange
    source: str
    target: str
    spot_buy: float | None = None
    spot_sell: float | None = None
    cash_buy: float | None = None
    cash_sell: float | None = None

    @field_validator("spot_buy", "spot_sell", "cash_buy", "cash_sell", mode="before")
    @classmethod
    def parse_float(cls, value: float | str | None) -> float | None:
        if value is None:
            return None

        if isinstance(value, float):
            if value == 0:
                return None
            return value

        value = float(value)
        if value == 0:
            return None
        return value

    @property
    def spot_mid(self) -> float | None:
        if self.spot_buy is None or self.spot_sell is None:
            logger.info("spot_buy or spot_sell is None")
            return None
        return (self.spot_buy + self.spot_sell) / 2

    @property
    def cash_mid(self) -> float | None:
        if self.cash_buy is None or self.cash_sell is None:
            logger.info("cash_buy or cash_sell is None")
            return None
        return (self.cash_buy + self.cash_sell) / 2

    @property
    def symbol(self) -> str:
        return f"{self.source}/{self.target}"

    @property
    def spot_spread(self) -> float | None:
        if self.spot_buy is None or self.spot_sell is None:
            logger.info("spot_buy or spot_sell is None")
            return None

        if self.spot_mid is None:
            logger.info("spot_mid is None")
            return None

        return (self.spot_sell - self.spot_buy) / self.spot_mid

    @property
    def cash_spread(self) -> float | None:
        if self.cash_mid is None:
            logger.info("cash_mid is None")
            return None

        if self.cash_buy is None or self.cash_sell is None:
            logger.info("cash_buy or cash_sell is None")
            return None

        return (self.cash_sell - self.cash_buy) / self.cash_mid
