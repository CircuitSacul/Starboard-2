import discord
from discord.ext import commands

from app import converters, errors, utils
from app.classes.bot import Bot


class AutoStarChannels(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.group(
        name="aschannels",
        aliases=["autostarchannels", "asc"],
        brief="List AutoStar Channels",
        invoke_without_command=True,
    )
    @commands.guild_only()
    async def aschannels(
        self, ctx: commands.Context, aschannel: converters.ASChannel = None
    ) -> None:
        """Lists all AutoStarChannels, or shows settings for a
        specific AutoStarChannel."""
        if not aschannel:
            p = utils.escmd(ctx.prefix)
            aschannels = await self.bot.db.get_aschannels(ctx.guild.id)

            if len(aschannels) == 0:
                await ctx.send(
                    "You do not have any AutoStarChannels. use "
                    f"`{p}asc add <channel>` to create one."
                )
                return

            embed = discord.Embed(
                title="AutoStarChannels",
                description=(
                    "This lists all AutoStarChannels and their most "
                    f"important settings. Use `{p}asc <aschannel>` to "
                    "view all settings."
                ),
                color=self.bot.theme_color,
            )
            for asc in aschannels:
                c = ctx.guild.get_channel(int(asc["id"]))
                emoji_str = utils.pretty_emoji_string(asc["emojis"], ctx.guild)
                embed.add_field(
                    name=c or f"Deleted Channel {asc['id']}",
                    value=(
                        f"emojis: **{emoji_str}**\n"
                        f"minChars: **{asc['min_chars']}**\n"
                        f"requireImage: **{asc['require_image']}**\n"
                    ),
                )

            await ctx.send(embed=embed)
        else:
            a = aschannel.sql
            c = aschannel.obj
            emoji_str = utils.pretty_emoji_string(a["emojis"], ctx.guild)
            embed = discord.Embed(
                title=f"{c.name}",
                description=(
                    f"emojis: **{emoji_str}**\n"
                    f"minChars: **{a['min_chars']}**\n"
                    f"requireImage: **{a['require_image']}**\n"
                    f"deleteInvalid: **{a['delete_invalid']}**\n"
                    f"regex: `{utils.escmd(a['regex']) or 'None'}`\n"
                    "excludeRegex: "
                    f"`{utils.escmd(a['exclude_regex']) or 'None'}`"
                ),
                color=self.bot.theme_color,
            )
            await ctx.send(embed=embed)

    @aschannels.command(
        name="add", aliases=["a", "+"], brief="Adds an AutoStarChannel"
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def add_aschannel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> None:
        """Creates an AutoStarChannel"""
        await self.bot.db.create_aschannel(channel.id, ctx.guild.id)
        await ctx.send(f"Created AutoStarChannel {channel.mention}")

    @aschannels.command(
        name="remove", aliases=["r", "-"], brief="Removes an AutoStarChannel"
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def remove_aschannel(
        self, ctx: commands.Context, aschannel: converters.ASChannel
    ) -> None:
        """Deletes an AutoStarChannel"""
        await self.bot.db.execute(
            """DELETE FROM aschannels
            WHERE id=$1""",
            aschannel.obj.id,
        )
        await ctx.send(f"Deleted AutoStarChannel {aschannel.obj.mention}.")

    @aschannels.group(
        name="emojis",
        aliases=["e"],
        brief="Modify the emojis for AutoStarChannels",
        invoke_without_command=True,
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def asemojis(self, ctx: commands.Context) -> None:
        p = utils.escmd(ctx.prefix)
        await ctx.send(
            "Options:\n"
            f" - {p}asc emojis add <aschannel> <emoji>\n"
            f" - {p}asc emojis remove <aschannel> <emoji>\n"
            f" - {p}asc emojis clear <aschannel>\n"
        )

    @asemojis.command(
        name="add", aliases=["a"], brief="Adds an emoji to an AutoStarChannel"
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def add_asemoji(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        emoji: converters.Emoji,
    ) -> None:
        clean = utils.clean_emoji(emoji)
        try:
            await self.bot.db.add_asemoji(aschannel.obj.id, clean)
        except errors.AlreadyExists:
            # Raise a more user-friendly error message
            raise errors.AlreadyExists(
                f"{emoji} is already an emoji on {aschannel.obj.mention}"
            )
        old = utils.pretty_emoji_string(aschannel.sql["emojis"], ctx.guild)
        new = utils.pretty_emoji_string(
            aschannel.sql["emojis"] + [emoji], ctx.guild
        )
        await ctx.send(
            embed=utils.cs_embed(
                {"emojis": (old, new)}, self.bot, noticks=True
            )
        )

    @asemojis.command(
        name="remove",
        aliases=["r", "d", "del", "delete"],
        brief="Removes an emojis from an AutoStarChannel",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def remove_asemoji(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        emoji: converters.Emoji,
    ) -> None:
        clean = utils.clean_emoji(emoji)
        try:
            await self.bot.db.remove_asemojis(aschannel.obj.id, clean)
        except errors.DoesNotExist:
            raise errors.DoesNotExist(
                f"{emoji} is not an emoji on {aschannel.obj.mention}"
            )
        _new = aschannel.sql["emojis"]
        old = utils.pretty_emoji_string(aschannel.sql["emojis"], ctx.guild)
        _new.remove(clean)
        new = utils.pretty_emoji_string(_new, ctx.guild)
        await ctx.send(
            embed=utils.cs_embed(
                {"emojis": (old, new)}, self.bot, noticks=True
            )
        )

    @asemojis.command(
        name="clear",
        aliases=["reset"],
        brief="Removes all emojis from an AutoStarChannel",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def clear_asemojis(
        self, ctx: commands.Context, aschannel: converters.ASChannel
    ) -> None:
        await ctx.send("Are you sure?")
        if not await utils.confirm(ctx):
            await ctx.send("Canncelled")
            return
        await self.bot.db.edit_aschannel(aschannel.obj.id, emojis=[])
        old = utils.pretty_emoji_string(aschannel.sql["emojis"], ctx.guild)
        await ctx.send(
            embed=utils.cs_embed({"emojis": (old, "None")}, self.bot)
        )

    @aschannels.command(
        name="minChars",
        aliases=["min", "mc"],
        brief="The minimum number of characters for messages",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def set_min_chars(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        min_chars: converters.myint,
    ) -> None:
        await self.bot.db.edit_aschannel(aschannel.obj.id, min_chars=min_chars)
        await ctx.send(
            embed=utils.cs_embed(
                {"minChars": (aschannel.sql["min_chars"], min_chars)}, self.bot
            )
        )

    @aschannels.command(
        name="requireImage",
        aliases=["imagesOnly", "ri"],
        brief="Whether or not messages must include an image",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def set_require_image(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        require_image: converters.mybool,
    ) -> None:
        await self.bot.db.edit_aschannel(
            aschannel.obj.id, require_image=require_image
        )
        await ctx.send(
            embed=utils.cs_embed(
                {
                    "requireImage": (
                        aschannel.sql["require_image"],
                        require_image,
                    )
                },
                self.bot,
            )
        )

    @aschannels.command(
        name="regex",
        aliases=["reg"],
        brief="A regex string that all messages must match",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def set_regex(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        regex: str,
    ) -> None:
        await self.bot.db.edit_aschannel(aschannel.obj.id, regex=regex)
        await ctx.send(
            embed=utils.cs_embed(
                {"regex": (aschannel.sql["regex"], regex)}, self.bot
            )
        )

    @aschannels.command(
        name="excludeRegex",
        alaises=["eregex", "ereg"],
        brief="A regex string that all messages must not match",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def set_eregex(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        exclude_regex: str,
    ) -> None:
        await self.bot.db.edit_aschannel(
            aschannel.obj.id, exclude_regex=exclude_regex
        )
        await ctx.send(
            embed=utils.cs_embed(
                {
                    "excludeRegex": (
                        aschannel.sql["exclude_regex"],
                        exclude_regex,
                    )
                },
                self.bot,
            )
        )

    @aschannels.command(
        name="deleteInvalid",
        aliases=["di"],
        brief="Whether or not to delete invalid messages",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def set_delete_invalid(
        self,
        ctx: commands.Context,
        aschannel: converters.ASChannel,
        delete_invalid: converters.mybool,
    ) -> None:
        await self.bot.db.edit_aschannel(
            aschannel.obj.id, delete_invalid=delete_invalid
        )
        await ctx.send(
            embed=utils.cs_embed(
                {
                    "deleteInvalid": (
                        aschannel.sql["delete_invalid"],
                        delete_invalid,
                    )
                },
                self.bot,
            )
        )


def setup(bot: Bot) -> None:
    bot.add_cog(AutoStarChannels(bot))