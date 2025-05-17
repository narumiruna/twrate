from __future__ import annotations

import os

from dotenv import find_dotenv
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger

from twrate import Exchange
from twrate import Rate
from twrate import fetch_rates


class RateWriter:
    @classmethod
    def from_env(cls) -> RateWriter:
        token = os.getenv("INFLUXDB_TOKEN")
        if token is None:
            raise ValueError("INFLUXDB_TOKEN is not set")

        org = os.getenv("INFLUXDB_ORG")
        if org is None:
            raise ValueError("INFLUXDB_ORG is not set")

        url = os.getenv("INFLUXDB_URL")
        if url is None:
            raise ValueError("INFLUXDB_URL is not set")

        bucket = os.getenv("INFLUXDB_BUCKET")
        if bucket is None:
            raise ValueError("INFLUXDB_BUCKET is not set")

        return cls(token=token, org=org, url=url, bucket=bucket)

    def __init__(self, *, token: str, org: str, url: str, bucket: str) -> None:
        self.org = org
        self.bucket = bucket
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def create_point(self, rate: Rate) -> Point:
        logger.info("[InfluxDB] creating point from: {}", rate)

        point = (
            Point("exchange_rates")
            .tag("exchange", rate.exchange.name.upper())
            .tag("source_currency", rate.source.upper())
            .tag("target_currency", rate.target.upper())
            .time(rate.fetched_at)
        )

        if rate.spot_buy:
            point = point.field("spot_buy", rate.spot_buy)

        if rate.spot_sell:
            point = point.field("spot_sell", rate.spot_sell)

        if rate.cash_buy:
            point = point.field("cash_buy", rate.cash_buy)

        if rate.cash_sell:
            point = point.field("cash_sell", rate.cash_sell)

        return point

    def create_points(self, rates: list[Rate]) -> list[Point]:
        return [self.create_point(rate) for rate in rates]

    def write_points(self, points: list[Point]) -> None:
        logger.info("[InfluxDB] writing points")
        self.write_api.write(bucket=self.bucket, org=self.org, record=points)

    def write_rates(self, rates: list[Rate]) -> None:
        points = self.create_points(rates)
        self.write_points(points)


def main() -> None:
    load_dotenv(find_dotenv())

    writer = RateWriter.from_env()

    rates = []
    for exchange in Exchange:
        rates.extend(fetch_rates(exchange))

    writer.write_rates(rates)


if __name__ == "__main__":
    main()
