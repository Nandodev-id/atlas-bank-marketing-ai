"""Run from the repository root with: uvicorn api.main:app --reload."""

import sys

from loguru import logger

from bank_marketing.service.app import create_app

logger.remove()
logger.add(sys.stderr, serialize=True)
app = create_app()
