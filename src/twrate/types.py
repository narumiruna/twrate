from pydantic import BaseModel
from pydantic import field_validator


class Rate(BaseModel):
    exchange: str
    source: str
    target: str
    spot_buy_rate: float | None = None
    spot_sell_rate: float | None = None
    cash_buy_rate: float | None = None
    cash_sell_rate: float | None = None

    @field_validator("spot_buy_rate", "spot_sell_rate", "cash_buy_rate", "cash_sell_rate", mode="before")
    @classmethod
    def convert_to_float(cls, value: float | str | None) -> float | None:
        if value is None:
            return None

        if isinstance(value, float):
            if value == 0:
                return None
            return value

        return float(value)

    @property
    def spot_mid_rate(self) -> float:
        if self.spot_buy_rate is None or self.spot_sell_rate is None:
            raise ValueError("spot_buy_rate and spot_sell_rate must be set to calculate mid rate")
        return (self.spot_buy_rate + self.spot_sell_rate) / 2

    @property
    def cash_mid_rate(self) -> float:
        if self.cash_buy_rate is None or self.cash_sell_rate is None:
            raise ValueError("cash_buy_rate and cash_sell_rate must be set to calculate mid rate")
        return (self.cash_buy_rate + self.cash_sell_rate) / 2

    @property
    def symbol(self) -> str:
        return f"{self.source}/{self.target}"
