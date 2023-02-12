import os
from logging import Logger

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.context.async_context import AsyncBoltContext

from webapp import configure_web_app

from .cmd import ping
from .cmd import ansible_vault
from .cmd import secret

BOT = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

SLACK_CMD = os.getenv("SLACK_CMD", "/opsbot")
USAGE = ""

""""
SUBCMDS is for matching subcommand to implementation module.
Each module could implement functions:
- handler(...), must have, subcommand handler
- get_cmd_usage(cmd, subcmd), optional, to get subcommand help
- configure_web_app(bot: AsyncApp), optional, configure
  aiohttp web app (routes, background tasks, etc)
"""
SUBCMDS: list[dict] = [
    {"subcmd": ["ping"], "module": ping},
    {"subcmd": ["ansible_vault"], "module": ansible_vault},
    {"subcmd": ["secret"], "module": secret},
]


def show_usage() -> str:
    return f"""Usage:{USAGE}"""


@BOT.command(SLACK_CMD)
async def cmd_opsbot(ack: AsyncAck, say: AsyncSay, respond: AsyncRespond,
                     body: dict, client: AsyncWebClient, payload: dict,
                     context: AsyncBoltContext, logger: Logger):
    global USAGE, SUBCMDS
    await ack()
    args = body["text"].split()
    if len(args) > 0:

        for item in SUBCMDS:
            if args[0] in item["subcmd"]:
                await item["module"].handler(ack, say, respond, body, client,
                                             payload, context, logger, args[1:])
                return

    await respond(show_usage())


def init():
    global USAGE, SUBCMDS, BOT

    # basic web configuration
    configure_web_app(BOT)

    # initialization of subcommand modules
    for item in SUBCMDS:
        for subcmd in item["subcmd"]:
            # run get_cmd_usage if implemented in the module
            if hasattr(item["module"], "get_cmd_usage"):
                USAGE = f"""{USAGE}{item["module"].get_cmd_usage(SLACK_CMD, subcmd)}"""

            # run configure_web_app if implemented in the module
            if hasattr(item["module"], "configure_web_app"):
                item["module"].configure_web_app(BOT)


# init package on import
init()
