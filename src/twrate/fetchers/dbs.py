from __future__ import annotations

from datetime import datetime

import httpx
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from ..types import Exchange
from ..types import Rate

# https://www.dbs.com.tw/personal-zh/rates/foreign-exchange-rates.page


class RecDatum(BaseModel):
    currency: str
    tt_sell: float = Field(..., validation_alias="ttSell")
    tt_buy: float = Field(..., validation_alias="ttBuy")
    cash_sell: float | None = Field(..., validation_alias="cashSell")
    cash_buy: float | None = Field(..., validation_alias="cashBuy")

    @field_validator("tt_sell", "tt_buy", "cash_sell", "cash_buy", mode="before")
    @classmethod
    def parse_float(cls, value: str | None) -> float | None:
        if value is None:
            return None
        return float(value)


class Asset(BaseModel):
    rec_data: list[RecDatum] = Field(..., validation_alias="recData")


class Results(BaseModel):
    assets: list[Asset]


class DBSRateResponse(BaseModel):
    total: int
    start: int
    included: int
    results: Results
    last_updated_date_and_time: datetime = Field(..., validation_alias="lastUpdatedDateAndTime")
    effective_date_and_time: datetime = Field(..., validation_alias="effectiveDateAndTime")

    @field_validator("total", "start", "included", mode="before")
    @classmethod
    def parse_int(cls, value: str) -> int:
        return int(value)

    @field_validator("last_updated_date_and_time", "effective_date_and_time", mode="before")
    @classmethod
    def parse_datetime(cls, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    def to_rates(self) -> list[Rate]:
        rates = []
        for asset in self.results.assets:
            for rec_data in asset.rec_data:
                rate = Rate(
                    exchange=Exchange.DBS,
                    source=rec_data.currency,
                    target="TWD",
                    spot_buy=rec_data.tt_buy,
                    spot_sell=rec_data.tt_sell,
                    cash_buy=rec_data.cash_buy,
                    cash_sell=rec_data.cash_sell,
                )
                rates.append(rate)
        return rates


def fetch_dbs_rates() -> list[Rate]:
    url = "https://www.dbs.com.tw/tw-rates-api/v1/api/twrates/latestForexRates"
    resp = httpx.get(url=url)
    resp.raise_for_status()
    return DBSRateResponse.model_validate(resp.json()).to_rates()
