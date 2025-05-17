from twrate.sinopac import query_sinopac_rates
from twrate.types import Rate


def test_query_sinopac_rates() -> None:
    rates = query_sinopac_rates()

    assert isinstance(rates, list)
    assert len(rates) > 0
    for rate in rates:
        assert isinstance(rate, Rate)
        assert rate.exchange == "sinopac"
        assert rate.target == "TWD"
        assert rate.symbol == f"{rate.source}/{rate.target}"

        if rate.spot_buy is not None and rate.spot_sell is not None:
            assert rate.spot_buy > 0
            assert rate.spot_sell > 0
            assert rate.spot_mid == (rate.spot_buy + rate.spot_sell) / 2

        if rate.cash_buy is not None and rate.cash_sell is not None:
            assert rate.cash_buy > 0
            assert rate.cash_sell > 0
            assert rate.cash_mid == (rate.cash_buy + rate.cash_sell) / 2
