from loguru import logger

from .fetchers.bot import fetch_bot_rates
from .fetchers.cathay import fetch_cathay_rates
from .fetchers.cooperative import fetch_cooperative_bank_rates
from .fetchers.dbs import fetch_dbs_rates
from .fetchers.esun import fetch_esun_rates
from .fetchers.firstbank import fetch_firstbank_rates
from .fetchers.fubon import fetch_fubon_rates
from .fetchers.hsbc import fetch_hsbc_rates
from .fetchers.kgi import fetch_kgi_rates
from .fetchers.landbank import fetch_landbank_rates
from .fetchers.line import fetch_line_rates
from .fetchers.megabank import fetch_megabank_rates
from .fetchers.nextbank import fetch_nextbank_rates
from .fetchers.sinopac import fetch_sinopac_rates
from .fetchers.taichung import fetch_taichung_rates
from .fetchers.taishin import fetch_taishin_rates
from .fetchers.yuanta import fetch_yuanta_rates
from .types import Exchange
from .types import Rate


async def fetch_rates(exchange: Exchange) -> list[Rate]:
    logger.debug("Fetching rates from {:12s}", exchange.name)

    handlers = {
        Exchange.SINOPAC: fetch_sinopac_rates,
        Exchange.ESUN: fetch_esun_rates,
        Exchange.LINE: fetch_line_rates,
        Exchange.BOT: fetch_bot_rates,
        Exchange.DBS: fetch_dbs_rates,
        Exchange.HSBC: fetch_hsbc_rates,
        Exchange.NEXT: fetch_nextbank_rates,
        Exchange.KGI: fetch_kgi_rates,
        Exchange.CATHAY: fetch_cathay_rates,
        Exchange.MEGABANK: fetch_megabank_rates,
        Exchange.FIRSTBANK: fetch_firstbank_rates,
        Exchange.LANDBANK: fetch_landbank_rates,
        Exchange.YUANTA: fetch_yuanta_rates,
        Exchange.TAISHIN: fetch_taishin_rates,
        Exchange.TAICHUNG: fetch_taichung_rates,
        Exchange.COOPERATIVE: fetch_cooperative_bank_rates,
        Exchange.FUBON: fetch_fubon_rates,
    }

    fetcher = handlers.get(exchange)
    if fetcher is None:
        raise ValueError(f"Unsupported exchange: {exchange}")

    return await fetcher()

