import os
import logging
from aiohttp import web

from slack import BOT

logging.basicConfig(level=os.getenv("LOG_LEVEL", logging.INFO))

if __name__ == "__main__":
    web.run_app(BOT.web_app(), port=int(os.getenv("HTTP_PORT", 8080)))
