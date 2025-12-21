import os
import sys
from typing import Final
from typing import cast

from loguru import logger

from .fetcher import fetch_rates
from .types import Exchange
from .types import Rate

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])  # ty:ignore[invalid-argument-type]
