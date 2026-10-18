import os
import sys
import uvicorn
from loguru import logger

logger.remove()
logger.add(sys.stderr, serialize=True)
uvicorn.run(
    "bank_marketing.service.app:create_app",
    factory=True,
    host=os.getenv("ATLAS_HOST", "127.0.0.1"),
    port=int(os.getenv("ATLAS_PORT", "8000")),
)
