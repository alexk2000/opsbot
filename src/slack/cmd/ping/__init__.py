from logging import Logger

from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.context.async_context import AsyncBoltContext


USAGE = ""


async def handler(ack: AsyncAck, say: AsyncSay, respond: AsyncRespond,
                  body: dict, client: AsyncWebClient, payload: dict,
                  context: AsyncBoltContext, logger: Logger, args: list[str]):
    await respond("OpsBot is :up: & :man-running:")


def get_cmd_usage(cmd, subcmd):
    global USAGE

    USAGE = f"""
    {cmd} {subcmd} (check if bot is up & running)

    """
    return USAGE
