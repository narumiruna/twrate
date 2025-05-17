from twrate.bot import query_bot_rates
from twrate.types import Rate


def test_query_bot_rates() -> None:
    rates = query_bot_rates()

    assert isinstance(rates, list)
    assert len(rates) > 0
    for rate in rates:
        assert isinstance(rate, Rate)
        assert rate.exchange == "BOT"
        assert rate.target == "TWD"
        assert rate.symbol == f"{rate.source}/{rate.target}"

        if rate.spot_buy_rate is not None and rate.spot_sell_rate is not None:
            assert rate.spot_buy_rate > 0
            assert rate.spot_sell_rate > 0
            assert rate.spot_mid_rate == (rate.spot_buy_rate + rate.spot_sell_rate) / 2

        if rate.cash_buy_rate is not None and rate.cash_sell_rate is not None:
            assert rate.cash_buy_rate > 0
            assert rate.cash_sell_rate > 0
            assert rate.cash_mid_rate == (rate.cash_buy_rate + rate.cash_sell_rate) / 2
