import discord
from discord.ext import commands

import asyncpg
from aiohttp import ClientSession

import glob
import typing

from os import environ
from dotenv import load_dotenv
load_dotenv()

from cogs.utils.constants import STARTUP_QUERY

async def getPrefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("uwu")(bot, message)

    q = bot._prefixes.get(message.guild.id, None)
    if q:
        return commands.when_mentioned_or(q)(bot, message)

    await bot.pool.execute("""
    INSERT INTO prefixes VALUES ($1, $2);
    """, message.guild.id, "uwu")

    return commands.when_mentioned_or("uwu")(bot, message)


class KanaContext(commands.Context):
    def predict_ansi(self, target: typing.Union[discord.Member, discord.User] = None) -> bool:
        target = target or self.message.author

        if isinstance(target, discord.User):
            return False

        if target.is_on_mobile() \
                or target.status is discord.Status.offline:
            return False

        return True


class Kana(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_context(self, message, *, cls=KanaContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        print(f'{self.user} is online, on discord.py - {discord.__version__}')

    async def setup_hook(self):
        self._uptime = discord.utils.utcnow().timestamp()
        self.session = ClientSession()
        self.pool = await asyncpg.create_pool(environ["PSQL_URI"])

        await self.pool.execute(STARTUP_QUERY)

        self._prefixes = {
            prefix["id"]: prefix["prefix"]
            for prefix in (
                    await bot.pool.fetch("SELECT * FROM prefixes;")
                )
            }

        await self.load_extension("jishaku")

        for cog in glob.glob("cogs/*.py", recursive=True):
            await self.load_extension(
                cog.replace("\\", ".").replace("/", ".").removesuffix(".py")
            )

    async def close(self):
        await super().close()
        await self.pool.close()
        await self.session.close()


bot = Kana(
    command_prefix=getPrefix,
    help_command=None, # i'm too lazy to subclass help so i'll just disable it for the time being
    case_insensitive=True,
    intents=discord.Intents().all(),
    strip_after_prefix=True
)

bot.run(environ["TOKEN"], reconnect=True)
