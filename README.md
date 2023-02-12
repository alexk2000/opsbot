# Operation Slack bot (OpsBot)

The idea of this bot is handle typical operations by issuing Slack command. Slack command **/opsbot** is used for this bot.

The first argument is subcommand. We are going to extend functionality of the bot by adding new subcommands.
Currently implemented subcommands are:

- ping (check if bot is ready to serve)
- ansible_vault (encrypt secret by ansible-vault command-line tool)
- secret (create short live link for one time access to the secret)

```
Usage:
    /opsbot ping (check if bot is up & running)
    /opsbot ansible_vault list keys (list of available keys)
    /opsbot ansible_vault encrypt <key name> <secret name> <secret> (encrypt secret)
    /opsbot secret <secret> (create short live link for one time access to the secret)
```

## Usage examples

- get help for all available subcommands

   `/opsbot`

   ```
   Usage:
      /opsbot ping (check if bot is up & running)
      /opsbot ansible_vault list keys (list of available keys)
      /opsbot ansible_vault encrypt <key name> <secret name> <secret> (encrypt secret)
      /opsbot secret <secret> (create short live link for one time access to the secret)
   ```

- subcommand **ansible_vault**:

   get list of available keys

   `/opsbot ansible_vault list keys`

   ```
   List of available keys: prod int dev
   ```

   encrypt secret by **prod** key

   `/opsbot ansible_vault encrypt prod my_secret_name my_super_strong_secret`

   ```
   my_secret_name: !vault |
            $ANSIBLE_VAULT;1.1;AES256
            63303361623763363765336363356432313834303430383136646232333361616666393137353761
            3136323237366435326561633663356664343235336665380a386662316433383638373562323132
            63373738636462376433333762646135663438343530656237653431336562306138333362636463
            3133383266653361320a663638363066393731323433346665643261373239303234303032376565
            35393636616231373538633735663033323132393165653332656232643030363231
   ```
- subcommand **secret**:

   create link to access secret

   `/opsbot secret mysupersecret2share`

   ```
   https://<OpsBot DNS name>/secret/18328be5-5c2b-4c8e-8d0b-2c816ae4bc0d
   ```

   send (via Slack, email etc) this link to colleague you want to share the secret, this link is available for 10 minutes and could be accessed only one time

   ```
   curl https://<OpsBot DNS name>/secret/18328be5-5c2b-4c8e-8d0b-2c816ae4bc0d

   mysupersecret2share

   curl https://<OpsBot DNS name>/secret/18328be5-5c2b-4c8e-8d0b-2c816ae4bc0d
   
   Not Found

   ```

## Prometheus metrics
If it's needed each subcommand could export Prometheus metrics regarding its usage ([code example](src/slack/cmd/secret/__init__.py#L31)).
Metrics endpoint - https://\<OpsBot DNS name\>/metrics.

```
# HELP opsbot_ansible_vault_encrypted_total total number of encrypted secrets
# TYPE opsbot_ansible_vault_encrypted_total counter
opsbot_ansible_vault_encrypted_total 3.0

# HELP opsbot_secrets_created_total total number of created secrets
# TYPE opsbot_secrets_created_total counter
opsbot_secrets_created_total 2.0

# HELP opsbot_secrets_expired_total total number of expired secrets
# TYPE opsbot_secrets_expired_total counter
opsbot_secrets_expired_total 0.0

# HELP opsbot_secrets_stored number of secrets stored in db now
# TYPE opsbot_secrets_stored gauge
opsbot_secrets_stored 0.0
```

## Python

OpsBot is build with Python using:

- [Slack Bold SDK](https://slack.dev/bolt-python/tutorial/getting-started) ([Python code examples](https://github.com/slackapi/bolt-python/tree/main/examples))
- [AIOHTTP](https://docs.aiohttp.org/en/stable/) (Python asynchronous web framework)
- [Python asynchronous programming](https://docs.python.org/3/library/asyncio.html)

## How to add new subcommands

New subcommand is separate [Python package](https://docs.python.org/3/tutorial/modules.html#packages) (directory with file \_\_init\_\_.py in it) which should be placed in package [cmd](src/slack/cmd/).
Two functions should be implemented in subcommand package:

- **handler** - mandatory, entry point to subcommand code

   ```
   async def handler(ack: AsyncAck, say: AsyncSay, respond: AsyncRespond,
                     body: dict, client: AsyncWebClient, payload: dict,
                     context: AsyncBoltContext, logger: Logger, args: list[str]):
   ```

- **get_cmd_usage** - optional, get subcommand usage to form global **/opsbot** command usage (when just run **/opsbot** without any arguments)

   ```
   def get_cmd_usage(cmd, subcmd)
   ```

- **configure_web_app** - optional, configure
  aiohttp web app (routes, background tasks, etc)
   ```
   def configure_web_app(bot: AsyncApp)
   ```

see [code of **secret** subcommand](src/slack/cmd/secret/__init__.py).

To create new subcommand you can use [ping subcommand](src/slack/cmd/ping) as a boilerplate code:

```
cp -a src/slack/cmd/ping src/slack/cmd/mynewsubcommand
```

and then import it and add to [list of subcommands](src/slack/__init__.py#L22).

```
from .cmd import mynewsubcommand
...

SUBCMDS: list[dict] = [
    ...
    {"subcmd": ["mynewsubcommand"], "module": mynewsubcommand},
]
```

## Health check and version endpoints

```
❯ curl https://<OpsBot DNS name>/health_check
{"status": "UP"}

❯ curl https://<OpsBot DNS name>/info
{"name": "opsbot", "version": "0.0.4"}
```
