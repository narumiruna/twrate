import os
import sys
from typing import Final

from loguru import logger

from .bot import fetch_bot_rates
from .dbs import fetch_dbs_rates
from .esun import fetch_esun_rates
from .line import fetch_line_rates
from .sinopac import fetch_sinopac_rates
from .types import Exchange
from .types import Rate

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])
