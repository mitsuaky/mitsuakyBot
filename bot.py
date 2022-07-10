import asyncio
import asyncpg
import discord
from aiohttp import ClientSession
from discord.ext import commands

from utils.config import Config
from utils.context import MitsuakyContext
from utils.logging import setup_logger

from loguru import logger


class MitBot(commands.Bot):
    def __init__(
        self,
        config: Config,
        db_pool: asyncpg.Pool,
        web_client: ClientSession,
    ):
        self.db_pool = db_pool
        self.web_client = web_client
        self.config = config

        allowed_mentions = discord.AllowedMentions(
            roles=False,
            everyone=False,
            users=True,
        )
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.config.bot.prefix),
            pm_help=None,
            chunk_guilds_at_startup=False,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
        )

    async def setup_hook(self):
        for extension in self.config.bot.initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception:
                logger.exception(f"Error while loading extension {extension}")

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

    async def on_message(self, message: discord.Message) -> None:
        ctx = await self.get_context(message, cls=MitsuakyContext)
        await self.invoke(ctx)


async def main():
    setup_logger()  # setup loguru
    config = Config()
    pool_kwargs = {
        "user": config.db.username,
        "password": config.db.password,
        "database": config.db.database_name,
        "command_timeout": 30,
    }

    async with asyncpg.create_pool(**pool_kwargs) as pool:
        async with ClientSession() as aio_client:
            async with MitBot(config, pool, aio_client) as bot:
                # load jishaku before everything else
                await bot.load_extension("jishaku")
                await bot.start(config.bot.token)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main())
