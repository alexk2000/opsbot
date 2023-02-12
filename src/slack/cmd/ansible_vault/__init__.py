import os
import asyncio
from logging import Logger

from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from slack_bolt.context.async_context import AsyncBoltContext

from prometheus_client import Counter

# read env vars
ANSIBLE_VAULT_KEYS_DIR = os.getenv(
    "ANSIBLE_VAULT_KEYS_DIR", os.getcwd() + "/ansible_vault_keys")
KEYS: list[str] = [f for f in os.listdir(ANSIBLE_VAULT_KEYS_DIR) if not f.startswith('.')]
APP_NAME = os.getenv("APP_NAME", "opsbot")

USAGE = ""

# metrics
ENCRYPTED_COUNTER = Counter(f"{APP_NAME}_ansible_vault_encrypted",
                            "total number of encrypted secrets", [])


async def handler(ack: AsyncAck, say: AsyncSay, respond: AsyncRespond,
                  body: dict, client: AsyncWebClient, payload: dict,
                  context: AsyncBoltContext, logger: Logger, args: list[str]):
    if len(args) > 0:
        if args[0] in ["ls", "list"]:
            await ls(respond, args[1:])
            return
        elif args[0] == "encrypt":
            await encrypt(respond, args[1:])
            return

    await respond(show_usage())


def get_cmd_usage(cmd: str, subcmd: str):
    global USAGE

    USAGE = f"""{cmd} {subcmd} list keys (list of available keys)
    {cmd} {subcmd} encrypt <key name> <secret name> <secret> (encrypt secret)"""

    return USAGE


def show_usage():
    global USAGE

    return f"""Usage:
    {USAGE}"""


async def ls(respond: AsyncRespond, args: list[str]):
    if len(args) > 0:
        if args[0] == "keys":
            await ls_keys(respond)
            return

    await respond(show_usage())


async def ls_keys(respond: AsyncRespond):
    await respond("List of available keys: `" + "` `".join(KEYS) + "`")


async def encrypt(respond: AsyncRespond, args: list[str]):
    if len(args) == 3:
        if args[0] in os.listdir(ANSIBLE_VAULT_KEYS_DIR):
            cmd = f"ansible-vault encrypt_string --vault-password-file {ANSIBLE_VAULT_KEYS_DIR}/{args[0]} --name {args[1]} {args[2]}"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if stdout:
                await respond("```" + stdout.decode() + "```")
                ENCRYPTED_COUNTER.inc()
            if stderr:
                await respond("```ERROR:\n" + stderr.decode() + "```")
            return
        else:
            await respond(f"Error: key `{args[0]}` doesn't exist")
            return

    await respond(show_usage())
