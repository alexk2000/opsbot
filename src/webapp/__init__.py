import os
import json

from aiohttp import web

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from prometheus_async import aio

SOCKET_MODE_CLIENT: SocketModeClient
APP_NAME = os.getenv("APP_NAME", "opsbot")
VERSION = ""


def configure_web_app(bot: AsyncApp):
    web_app = bot.web_app()

    web_app.add_routes([
        web.get("/health_check", health_check),
        web.get("/info", info),
        web.get("/metrics", aio.web.server_stats)
    ])

    async def start_socket_mode(web_app: web.Application):
        handler = AsyncSocketModeHandler(bot, os.environ["SLACK_APP_TOKEN"])
        await handler.connect_async()
        global SOCKET_MODE_CLIENT
        SOCKET_MODE_CLIENT = handler.client

    async def shutdown_socket_mode(web_app: web.Application):
        await SOCKET_MODE_CLIENT.close()

    web_app.on_startup.append(start_socket_mode)
    web_app.on_shutdown.append(shutdown_socket_mode)


async def health_check(req: web.Request) -> web.Response:
    if SOCKET_MODE_CLIENT is not None and await SOCKET_MODE_CLIENT.is_connected():
        return web.json_response(status=200, data={"status": "UP"})
    return web.json_response(
        status=503, data={"status": "DOWN", "error": "no connection to Slack"})


async def info(req: web.Request) -> web.Response:
    return web.json_response(status=200, data={"name": APP_NAME, "version": VERSION})


def get_version_from_package_json():
    try:
        return json.load(open("package.json"))["version"]
    except Exception:
        return ""


def init():
    global VERSION

    VERSION = get_version_from_package_json()


# init package on import
init()
