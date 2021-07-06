import discord

from app import commands
from app.classes.bot import Bot


class CacheEvents(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(
        self, payload: discord.RawMessageDeleteEvent
    ) -> None:
        if not payload.guild_id:
            return
        if payload.message_id in self.bot.cache.messages:
            del self.bot.cache.messages[payload.message_id]

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: discord.RawBulkMessageDeleteEvent
    ) -> None:
        if not payload.guild_id:
            return
        for mid in payload.message_ids:
            if mid in self.bot.cache.messages:
                del self.bot.cache.messages[mid]


def setup(bot: Bot) -> None:
    bot.add_cog(CacheEvents(bot))
