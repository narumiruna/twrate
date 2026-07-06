from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from typing import Literal

import httpx
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from ..types import Exchange
from ..types import Rate


class HeadInfoItem(BaseModel):
    head_text: str = Field(..., validation_alias="HeadText")
    head_align: str = Field(..., validation_alias="HeadAlign")
    data_align: str = Field(..., validation_alias="DataAlign")
    main_show: str = Field(..., validation_alias="MainShow")
    detail_show: str = Field(..., validation_alias="DetailShow")
    field_key: str = Field(..., validation_alias="FieldKey")
    order_index: str = Field(..., validation_alias="OrderIndex")
    field_width: str = Field(..., validation_alias="FieldWidth")


class SubInfoItem(BaseModel):
    data_value1: str = Field(..., validation_alias="DataValue1")
    data_value1_img: str = Field(..., validation_alias="DataValue1Img")
    data_value2: float | None = Field(..., validation_alias="DataValue2")
    data_value3: float | None = Field(..., validation_alias="DataValue3")
    data_value4: str = Field(..., validation_alias="DataValue4")

    @field_validator("data_value2", "data_value3", mode="before")
    @classmethod
    def parse_float(cls, value: Any) -> float | None:
        if value is None or value == "-":
            return None
        if isinstance(value, bool):
            raise ValueError("rate value must be numeric, not boolean")
        return float(value)


class SinopacRateResponse(BaseModel):
    title_info: str = Field(..., validation_alias="TitleInfo")
    query_date: datetime = Field(..., validation_alias="QueryDate")
    head_info: list[HeadInfoItem] = Field(..., validation_alias="HeadInfo")
    sub_info: list[SubInfoItem] = Field(..., validation_alias="SubInfo")
    memo_url: Any = Field(None, validation_alias="MemoUrl")
    header: str = Field(..., validation_alias="Header")
    message: str = Field(..., validation_alias="Message")

    @field_validator("query_date", mode="before")
    @classmethod
    def parse_datetime(cls, value: str) -> datetime:
        return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")


def _build_sinopac_rate(item: SubInfoItem, exchange_type: Literal["cash", "remit"]) -> Rate:
    match exchange_type:
        case "remit":
            return Rate(
                exchange=Exchange.SINOPAC,
                source=item.data_value4,
                target="TWD",
                spot_buy=item.data_value2,
                spot_sell=item.data_value3,
            )
        case "cash":
            return Rate(
                exchange=Exchange.SINOPAC,
                source=item.data_value4,
                target="TWD",
                cash_buy=item.data_value2,
                cash_sell=item.data_value3,
            )


def merge_rates(*, remit_rates: list[Rate], cash_rates: list[Rate]) -> list[Rate]:
    result: dict[str, Rate] = {}

    for rate in remit_rates:
        key = f"{rate.source}/{rate.target}"
        if key not in result:
            result[key] = rate
            continue

        result[key].spot_buy = rate.spot_buy
        result[key].spot_sell = rate.spot_sell

    for rate in cash_rates:
        key = f"{rate.source}/{rate.target}"
        if key not in result:
            result[key] = rate
            continue

        result[key].cash_buy = rate.cash_buy
        result[key].cash_sell = rate.cash_sell

    return list(result.values())


async def fetch_sinopac_rates(exchange_type: Literal["cash", "remit", "all"] = "all") -> list[Rate]:
    """Query SinoPac exchange rates.

    Args:
        exchange_type (str): The type of exchange rate to query. Can be "cash", "remit", or "all".

    Returns a list of Rate objects with the exchange rates for various currencies.
    """
    if exchange_type not in {"cash", "remit", "all"}:
        raise ValueError(f"Invalid exchange type: {exchange_type}")

    if exchange_type == "all":
        remit_rates, cash_rates = await asyncio.gather(
            fetch_sinopac_rates("remit"),
            fetch_sinopac_rates("cash"),
        )
        return merge_rates(
            remit_rates=remit_rates,
            cash_rates=cash_rates,
        )

    ts = int(datetime.now().timestamp() * 1000)
    url = f"https://m.sinopac.com/ws/share/rate/ws_exchange.ashx?{ts}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data={"exchangeType": exchange_type.upper()})
        resp.raise_for_status()

        data = [SinopacRateResponse.model_validate(item) for item in resp.json()]
        if len(data) != 1:
            raise ValueError("Failed to parse response")

        if data[0].header != "SUCCESS":
            raise ValueError("Failed to query rates")

        rates = []
        for item in data[0].sub_info:
            rates.append(_build_sinopac_rate(item, exchange_type))

        return rates
