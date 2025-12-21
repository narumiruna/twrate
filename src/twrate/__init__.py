import os
import sys
from typing import Any
from typing import Final
from typing import cast

from loguru import HandlerConfig
from loguru import logger

from .fetcher import fetch_rates
from .types import Exchange
from .types import Rate

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[cast(HandlerConfig, {"sink": sys.stderr, "level": LOGURU_LEVEL})])
