import os
import sys
from typing import Final

from loguru import logger

from .fetchers import fetch_rates
from .types import Exchange
from .types import Rate

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])
