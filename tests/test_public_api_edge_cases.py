import pytest

from twrate.fetcher import fetch_rates
from twrate.types import Exchange
from twrate.types import Rate


@pytest.mark.asyncio
async def test_fetch_rates_accepts_exchange_name_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch() -> list[Rate]:
        return []

    monkeypatch.setattr("twrate.fetcher.fetch_bot_rates", fake_fetch)

    assert await fetch_rates("BOT") == []


@pytest.mark.asyncio
async def test_fetch_rates_rejects_invalid_exchange_strings_before_logging() -> None:
    with pytest.raises(ValueError, match="Unsupported exchange"):
        await fetch_rates("not-a-bank")


@pytest.mark.asyncio
async def test_fetch_rates_accepts_exchange_value_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch() -> list[Rate]:
        return []

    monkeypatch.setattr("twrate.fetcher.fetch_bot_rates", fake_fetch)

    assert await fetch_rates(Exchange.BOT.value) == []
