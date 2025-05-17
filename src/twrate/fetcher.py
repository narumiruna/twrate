from .fetchers.bot import fetch_bot_rates
from .fetchers.dbs import fetch_dbs_rates
from .fetchers.esun import fetch_esun_rates
from .fetchers.line import fetch_line_rates
from .fetchers.sinopac import fetch_sinopac_rates
from .types import Exchange
from .types import Rate


def fetch_rates(exchange: Exchange) -> list[Rate]:
    match exchange:
        case Exchange.SINOPAC:
            return fetch_sinopac_rates()
        case Exchange.ESUN:
            return fetch_esun_rates()
        case Exchange.LINE:
            return fetch_line_rates()
        case Exchange.BOT:
            return fetch_bot_rates()
        case Exchange.DBS:
            return fetch_dbs_rates()
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
