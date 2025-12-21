from loguru import logger

from .fetchers.bot import fetch_bot_rates
from .fetchers.dbs import fetch_dbs_rates
from .fetchers.esun import fetch_esun_rates
from .fetchers.hsbc import fetch_hsbc_rates
from .fetchers.line import fetch_line_rates
from .fetchers.sinopac import fetch_sinopac_rates
from .types import Exchange
from .types import Rate


async def fetch_rates(exchange: Exchange) -> list[Rate]:
    logger.info("Fetching rates from {}", exchange.name)
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
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
