from logging import Logger
from aiohttp import web
import asyncio
import uuid
import os
import time
import logging

from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.app.async_app import AsyncApp

from prometheus_client import Counter, Gauge

# read env vars
MY_URL = os.getenv("MY_URL", "http://localhost:8080")
APP_NAME = os.getenv("APP_NAME", "opsbot")
SECRET_TTL = int(os.getenv("SECRET_TTL", "600"))
""" check SECRET_STORAGE every SECRET_CLEANUP_PERIOD seconds
to find/remove expired secrets """
SECRET_CLEANUP_PERIOD = int(os.getenv("SECRET_CLEANUP_PERIOD", "10"))

USAGE = ""

SECRET_STORAGE_LOCK = asyncio.Lock()
SECRET_STORAGE: dict[str, dict] = {}

# metrics
SECRETS_COUNTER = Counter(f"{APP_NAME}_secrets_created",
                          "total number of created secrets", [])
SECRETS_EXPIRED_COUNTER = Counter(f"{APP_NAME}_secrets_expired",
                                  "total number of expired secrets", [])
SECRETS_STORED = Gauge(f"{APP_NAME}_secrets_stored",
                       "number of secrets stored in db now", [])


async def handler(ack: AsyncAck, say: AsyncSay, respond: AsyncRespond,
                  body: dict, client: AsyncWebClient, payload: dict,
                  context: AsyncBoltContext, logger: Logger, args: list[str]):
    global SECRET_STORAGE_LOCK, SECRET_STORAGE, MY_URL, SECRETS_COUNTER

    if len(args) > 0:
        secret_uuid = str(uuid.uuid4())
        async with SECRET_STORAGE_LOCK:
            SECRET_STORAGE[secret_uuid] = {
                "secret": payload["text"].split(maxsplit=1)[1],
                "ts": time.time()}
            SECRETS_COUNTER.inc()
        return await respond(f"{MY_URL}/secret/{secret_uuid}")

    await respond(show_usage())


def get_cmd_usage(cmd: str, subcmd: str):
    global USAGE

    USAGE = f"""
    {cmd} {subcmd} <secret> (create short live link for one time access to the secret)

    """
    return USAGE


def show_usage():
    global USAGE

    return f"""Usage:
    {USAGE}"""


def configure_web_app(bot: AsyncApp):
    web_app = bot.web_app()

    web_app.add_routes([
        web.get("/secret/{secret_uuid}", get_secret),
    ])

    web_app.cleanup_ctx.append(setup_bg_task_secret_cleaner)


async def get_secret(req: web.Request) -> web.Response:
    global SECRET_STORAGE_LOCK, SECRET_STORAGE

    response: web.Response = web.Response(status=404, text="Not Found")

    async with SECRET_STORAGE_LOCK:
        if req.match_info["secret_uuid"] in SECRET_STORAGE:
            response = web.Response(
                status=200,
                text=SECRET_STORAGE.pop(req.match_info["secret_uuid"])["secret"])

    return response


async def setup_bg_task_secret_cleaner(web_app: web.Application):
    # on start
    web_app['bg_task_secret_cleaner'] = asyncio.create_task(bg_task_secret_cleaner(web_app))

    yield

    # on stop
    web_app['bg_task_secret_cleaner'].cancel()
    await web_app['bg_task_secret_cleaner']


async def bg_task_secret_cleaner(web_app: web.Application):
    global SECRET_TTL, SECRET_CLEANUP_PERIOD, SECRET_STORAGE_LOCK
    global SECRET_STORAGE, SECRETS_EXPIRED_COUNTER, SECRETS_STORED

    while True:
        await asyncio.sleep(SECRET_CLEANUP_PERIOD)
        logging.debug("secret cleaner started")
        async with SECRET_STORAGE_LOCK:
            cur_ts = time.time()
            expired = []
            for secret_uuid, secret in SECRET_STORAGE.items():
                if (cur_ts - secret["ts"]) >= SECRET_TTL:
                    expired.append(secret_uuid)

            for secret_uuid in expired:
                del SECRET_STORAGE[secret_uuid]
                SECRETS_EXPIRED_COUNTER.inc()
                logging.info(f"secret with id {secret_uuid} has expired (removed)")

            SECRETS_STORED.set(len(SECRET_STORAGE.keys()))
