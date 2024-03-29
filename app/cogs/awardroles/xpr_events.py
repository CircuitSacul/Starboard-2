import asyncio
from typing import TYPE_CHECKING, Dict, List

import discord
from discord.ext import tasks

from app import commands
from app.cogs.permroles import pr_functions
from app.i18n import t_

if TYPE_CHECKING:
    from app.classes.bot import Bot


async def set_xp_roles(
    to_add: List[int], to_remove: List[int], member: discord.Member
):
    curr = [r.id for r in member.roles]
    to_add = [member.guild.get_role(r) for r in to_add if r not in curr]
    to_remove = [member.guild.get_role(r) for r in to_remove if r in curr]
    try:
        await member.remove_roles(*to_remove)
        await member.add_roles(*to_add)
    except discord.Forbidden:
        pass


class XPREvents(commands.Cog):
    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.queue: Dict[int, List[int]] = {}
        self.update_xpr_loop.start()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        xprole = await self.bot.db.xproles.get(role.id)

        if not xprole:
            return

        await self.bot.db.xproles.delete(role.id)
        self.bot.dispatch(
            "guild_log",
            t_(
                f"The role `{role.name}` was deleted, so "
                "I removed that XPRole."
            ),
            "info",
            role.guild,
        )

    @commands.Cog.listener()
    async def on_update_xpr(self, guild_id: int, user_id: int):
        self.queue.setdefault(guild_id, [])
        self.queue[guild_id].append(user_id)

    @tasks.loop(seconds=5)
    async def update_xpr_loop(self):
        tasks: List[asyncio.Task] = []
        for gid in list(self.queue.keys()):
            to_update = self.queue[gid]
            if len(to_update) == 0:
                del self.queue[gid]
                continue
            n = to_update.pop()
            guild = self.bot.get_guild(gid)
            _member = await self.bot.cache.get_members([n], guild)
            if n not in _member:
                continue
            member = _member[n]

            perms = await pr_functions.get_perms(
                self.bot,
                [r.id for r in member.roles],
                member.guild.id,
                None,
                None,
            )

            if perms["xp_roles"]:
                sql_member = await self.bot.db.members.get(
                    member.id, member.guild.id
                )
                to_add = [
                    int(r["role_id"])
                    for r in await self.bot.db.fetch(
                        """SELECT * FROM xproles
                        WHERE guild_id=$1
                        AND required <= $2
                        ORDER BY required DESC""",
                        gid,
                        sql_member["xp"],
                    )
                ]
                sql_guild = await self.bot.db.guilds.get(guild.id)
                to_remove = [
                    int(r["role_id"])
                    for r in await self.bot.db.fetch(
                        """SELECT * FROM xproles
                        WHERE guild_id=$1
                        AND required > $2""",
                        gid,
                        sql_member["xp"],
                    )
                ]
                if not sql_guild["stack_xp_roles"]:
                    if len(to_add) > 1:
                        to_remove.extend(to_add[1:])
                        to_add = [to_add[0]]

            else:
                to_add = []
                to_remove = [
                    int(r["role_id"])
                    for r in (
                        await self.bot.db.execute(
                            """SELECT * FROM xproles
                        WHERE guild_id=$1""",
                            gid,
                        )
                        or []
                    )
                ]
            t = asyncio.create_task(set_xp_roles(to_add, to_remove, member))
            tasks.append(t)


def setup(bot: "Bot"):
    bot.add_cog(XPREvents(bot))
