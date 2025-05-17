from pydantic import BaseModel
from pydantic import field_validator


class Rate(BaseModel):
    exchange: str
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
    def spot_mid(self) -> float:
        if self.spot_buy is None or self.spot_sell is None:
            raise ValueError("spot_buy and spot_sell must be set to calculate mid rate")
        return (self.spot_buy + self.spot_sell) / 2

    @property
    def cash_mid(self) -> float:
        if self.cash_buy is None or self.cash_sell is None:
            raise ValueError("cash_buy and cash_sell must be set to calculate mid rate")
        return (self.cash_buy + self.cash_sell) / 2

    @property
    def symbol(self) -> str:
        return f"{self.source}/{self.target}"
