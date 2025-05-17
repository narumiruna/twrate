from pydantic import BaseModel


class Rate(BaseModel):
    exchange: str
    source: str
    target: str
    spot_buy_rate: float | None = None
    spot_sell_rate: float | None = None
    cash_buy_rate: float | None = None
    cash_sell_rate: float | None = None

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
