from __future__ import annotations

import httpx
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from .types import Exchange
from .types import Rate


class EsunRate(BaseModel):
    name: str = Field(..., validation_alias="Name")
    b_board_rate: float = Field(..., validation_alias="BBoardRate")
    s_board_rate: float = Field(..., validation_alias="SBoardRate")
    cash_b_board_rate: float | None = Field(..., validation_alias="CashBBoardRate")
    cash_s_board_rate: float | None = Field(..., validation_alias="CashSBoardRate")
    buy_increase_rate: float | None = Field(..., validation_alias="BuyIncreaseRate")
    sell_decrease_rate: float | None = Field(..., validation_alias="SellDecreaseRate")
    update_time: str = Field(..., validation_alias="UpdateTime")
    ccy: str = Field(..., validation_alias="CCY")
    key: str = Field(..., validation_alias="Key")
    url: str | None = Field(..., validation_alias="Url")
    title: str | None = Field(..., validation_alias="Title")
    serial: int = Field(..., validation_alias="Serial")
    alt: str | None = Field(..., validation_alias="Alt")
    bonus: str = Field(..., validation_alias="Bonus")
    cash_bonus: str | None = Field(..., validation_alias="CashBonus")
    description: str | None = Field(..., validation_alias="Description")

    @field_validator("cash_b_board_rate", "cash_s_board_rate", "buy_increase_rate", "sell_decrease_rate", mode="before")
    @classmethod
    def parse_float(cls, value: str) -> float | None:
        if value == "-" or value == "":
            return None
        return float(value)


class EsunRateResponse(BaseModel):
    discont_flag: str = Field(..., validation_alias="DiscontFlag")
    rates: list[EsunRate] = Field(..., validation_alias="Rates")
    time: list[str] = Field(..., validation_alias="Time")
    date: str = Field(..., validation_alias="Date")
    count: int = Field(..., validation_alias="Count")
    clear: int = Field(..., validation_alias="Clear")


def fetch_esun_rates() -> list[Rate]:
    url = "https://www.esunbank.com/api/client/ExchangeRate/LastRateInfo"

    resp = httpx.post(url)
    resp.raise_for_status()

    data = EsunRateResponse.model_validate(resp.json())

    rates = []
    for r in data.rates:
        rate = Rate(
            exchange=Exchange.ESUN,
            source=r.ccy.split("/")[0].upper(),
            target=r.ccy.split("/")[1].upper(),
            spot_buy=r.b_board_rate,
            spot_sell=r.s_board_rate,
            cash_buy=r.cash_b_board_rate,
            cash_sell=r.cash_s_board_rate,
        )
        rates.append(rate)
    return rates
