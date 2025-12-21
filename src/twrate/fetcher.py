from loguru import logger

from .fetchers.bot import fetch_bot_rates
from .fetchers.cathay import fetch_cathay_rates
from .fetchers.dbs import fetch_dbs_rates
from .fetchers.esun import fetch_esun_rates
from .fetchers.hsbc import fetch_hsbc_rates
from .fetchers.kgi import fetch_kgi_rates
from .fetchers.line import fetch_line_rates
from .fetchers.nextbank import fetch_nextbank_rates
from .fetchers.sinopac import fetch_sinopac_rates
from .types import Exchange
from .types import Rate


async def fetch_rates(exchange: Exchange) -> list[Rate]:
    logger.debug("Fetching rates from {:12s}", exchange.name)
    match exchange:
        case Exchange.SINOPAC:
            return await fetch_sinopac_rates()
        case Exchange.ESUN:
            return await fetch_esun_rates()
        case Exchange.LINE:
            return await fetch_line_rates()
        case Exchange.BOT:
            return await fetch_bot_rates()
        case Exchange.DBS:
            return await fetch_dbs_rates()
        case Exchange.HSBC:
            return await fetch_hsbc_rates()
        case Exchange.NEXT:
            return await fetch_nextbank_rates()
        case Exchange.KGI:
            return await fetch_kgi_rates()
        case Exchange.CATHAY:
            return await fetch_cathay_rates()
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
