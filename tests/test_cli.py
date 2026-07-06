from twrate import cli
from twrate.types import Exchange
from twrate.types import Rate


def test_run_strips_and_normalizes_source_currency(monkeypatch) -> None:
    async def fake_fetch_all_rates() -> list[Rate]:
        return [Rate(exchange=Exchange.BOT, source="USD", target="TWD", spot_buy=31.1, spot_sell=31.3)]

    printed = []

    class FakeConsole:
        def print(self, value) -> None:
            printed.append(value)

    monkeypatch.setattr(cli, "fetch_all_rates", fake_fetch_all_rates)
    monkeypatch.setattr(cli, "Console", FakeConsole)

    cli.run(" usd ")

    assert len(printed) == 1
    assert printed[0].title == "USD 各行即時牌價"
    assert len(printed[0].rows) == 1
