import discord
import os
import datetime
import json
import re
import time
import asyncio
from typing import Union
from discord.ext import tasks
from discord import Option, AllowedMentions, Embed
from discord.ext import commands
from logger import Logger
from main import guild_list, EMBED_COLOR, ARC_ICON_URL

log = Logger().log

with open("db.json", "r") as f:
    options = json.load(f)["options"]

    permissionList = options["permissionList"]
    default_mute_time = options["defaultMuteTime"]
    mute_role_id = options["muteRoleId"]
    # messages from one person over 5 seconds
    spam_limit = options["spamLimit"]
    banned_words = options["bannedWords"]
    audit_channel_id = options["auditChannelId"]


def parse_time_string(time_str: str) -> int:

    pattern = r'(?:(\d+)y)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, time_str)

    if match:
        years, days, hours, minutes, seconds = map(
            lambda x: int(x) if x is not None else 0, match.groups())

        total_seconds = (years * 31557600) + (days * 86400) + \
            (hours * 3600) + (minutes * 60) + seconds

        # greater than 32 bit epoch limit, arbitrary limit bc i dont want to
        # find Discord's limit
        if time.time() + total_seconds > 2147483647:
            return -1

        return total_seconds
    else:
        return -1


def seconds_to_time_string(total_seconds: int) -> str:

    if total_seconds <= 0:
        return "invalid"

    # years are in Julian years to account for leap years
    years, remaining_seconds = divmod(total_seconds, 31557600)
    days, remaining_seconds = divmod(remaining_seconds, 86400)
    hours, remaining_seconds = divmod(remaining_seconds, 3600)
    minutes, seconds = divmod(remaining_seconds, 60)

    time_str = ""
    if years > 0:
        time_str += f"{years}y"
    if days > 0:
        time_str += f"{days}d"
    if hours > 0:
        time_str += f"{hours}h"
    if minutes > 0:
        time_str += f"{minutes}m"
    if seconds > 0 or not time_str:
        time_str += f"{seconds}s"

    return time_str


def get_offset_time():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=-4)


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.unmute_loop.start()

    def cog_unload(self):
        self.unmute_loop.stop()

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["role"]))
    @discord.option("_type", type=str, description="Change to make.",
                    choices=["add", "remove"], required=True)
    @discord.option("member",
                    type=discord.Member,
                    description="Member to change role of.",
                    required=True)
    @discord.option("role",
                    type=discord.Role,
                    description="Role to change.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for change.",
                    required=False)
    async def role(
        self,
        ctx: discord.ApplicationContext,
        _type: str,
        member: discord.Member,
        role: discord.Role,
        reason: Union[str, None]
    ):

        """

        Add or remove a role from a member.

        Args:
            change (str): Change to make.
            member (discord.Member): Member to change role of.
            role (discord.Role): Role to change.
            reason (str|None): Reason for change.

        Returns:
            None

        """

        reason = reason if reason else "None"
        audit_reason = f"By {ctx.author.name}({ctx.author.id}) for: {reason}"

        if _type == "add":

            if role in member.roles:
                msg = discord.Embed(
                    title="Role Add",
                    description=f"{member.mention} already has {role.mention}.",
                    color=EMBED_COLOR,
                    timestamp=get_offset_time())
                msg.set_footer(
                    text=f"Requested by {ctx.author.name}",
                    icon_url=ctx.author.display_avatar)

                return await ctx.response.send_message(embed=msg)

            await member.add_roles(role, reason=audit_reason)

            msg = discord.Embed(
                title="Role Add",
                description=f"Added {role.mention} to {member.mention}.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            await ctx.response.send_message(embed=msg)

            # I would love to do this in a better way but I can't find a way to
            # get the message object from the response
            response_msg = (await ctx.channel.history(limit=1).flatten())[0]

            audit_msg = Embed(
                title="Link to action",
                url=response_msg.jump_url,
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            audit_msg.set_author(name=f"Moderation - Role Add")
            audit_msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)
            audit_msg.add_field(
                name="Moderator",
                value=f"{ctx.author.mention}",
                inline=True)
            audit_msg.add_field(
                name="Recipient",
                value=member.mention,
                inline=True)
            audit_msg.add_field(name="Role", value=role.mention, inline=True)
            audit_msg.add_field(name="Reason", value=reason, inline=False)
            audit_msg.add_field(
                name="Timestamp",
                value=f"`{get_offset_time().isoformat()}`",
                inline=False)

            await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

            log("moderation", __name__,
                f"{ctx.author.name}({ctx.author.id}) added role {role.name}({role.id}) to {member.name}({member.id}).")

        elif _type == "remove":

            if role not in member.roles:
                msg = discord.Embed(
                    title="Role Remove",
                    description=f"{member.mention} does not have {role.mention}.",
                    color=EMBED_COLOR,
                    timestamp=get_offset_time())
                msg.set_footer(
                    text=f"Requested by {ctx.author.name}",
                    icon_url=ctx.author.display_avatar)

                return await ctx.response.send_message(embed=msg)

            await member.remove_roles(role, reason=reason)

            msg = discord.Embed(
                title="Role Remove",
                description=f"Removed {role.mention} from {member.mention}.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            # TODO: Generalize next 13 lines
            await ctx.response.send_message(embed=msg)

            # I would love to do this in a better way but I can't find a way to
            # get the message object from the response
            response_msg = (await ctx.channel.history(limit=1).flatten())[0]

            audit_msg = Embed(
                title="Link to action",
                url=response_msg.jump_url,
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            audit_msg.set_author(name=f"Moderation - Role Remove")
            audit_msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)
            audit_msg.add_field(
                name="Moderator",
                value=ctx.author.mention,
                inline=True)
            audit_msg.add_field(
                name="Recipient",
                value=member.mention,
                inline=True)
            audit_msg.add_field(name="Role", value=role.mention, inline=True)
            audit_msg.add_field(name="Reason", value=reason, inline=False)
            audit_msg.add_field(
                name="Timestamp",
                value=f"`{get_offset_time().isoformat()}`",
                inline=False)

            await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

            log("moderation", __name__,
                f"{ctx.author.name}({ctx.author.id}) removed role {role.name}({role.id}) from {member.name}({member.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["ban"]))
    @discord.option("user",
                    type=discord.User,
                    description="User to ban.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for ban.",
                    required=False)
    async def ban(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User,
        reason: Union[str, None]
    ):

        """

        Ban a member.

        Args:
            user (discord.User): User to ban.
            reason (str|None): Reason for ban.

        Returns:
            None

        """

        audit_reason = reason if reason else 'None'
        reason = f"By {ctx.author.name}({ctx.author.id}) for: {audit_reason}"

        bans = await ctx.guild.bans().flatten()

        if user in [ban.user for ban in bans]:
            msg = discord.Embed(
                title="Ban",
                description=f"{user.mention} is already banned.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        if user == ctx.author:
            msg = discord.Embed(
                title="Ban",
                description=f"You can't ban yourself :O",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        await ctx.guild.ban(user=user, reason=reason)

        msg = discord.Embed(
            title="Ban",
            description=f"Banned {user.mention}.",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Ban")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(name="Recipient", value=user.mention, inline=True)
        audit_msg.add_field(name="Reason", value=audit_reason, inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) banned {user.name}({user.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["ban"]))
    @discord.option("user",
                    type=discord.User,
                    description="User to unban.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for unban.",
                    required=False)
    async def unban(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User,
        reason: Union[str, None]
    ):

        """

        Unban a user.

        Args:
            user (discord.User): User to unban.
            reason (str|None): Reason for unban.

        Returns:
            None

        """

        audit_reason = reason if reason else 'None'
        reason = f"By {ctx.author.name}({ctx.author.id}) for: {audit_reason}"

        bans = await ctx.guild.bans().flatten()

        if user not in [ban.user for ban in bans]:
            msg = discord.Embed(
                title="Unban",
                description=f"{user.mention} is not banned.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        await ctx.guild.unban(user=user, reason=reason)

        msg = discord.Embed(
            title="Unban",
            description=f"Unbanned {user.mention}.",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Unban")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(name="Recipient", value=user.mention, inline=True)
        audit_msg.add_field(name="Reason", value=audit_reason, inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) unbanned {user.name}({user.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["kick"]))
    @discord.option("member",
                    type=discord.Member,
                    description="Member to kick.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for kick.",
                    required=False)
    async def kick(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        reason: Union[str, None]
    ):

        """

        Kick a member.

        Args:
            member (discord.Member): Member to kick.
            reason (str|None): Reason for kick.

        Returns:
            None

        """

        audit_reason = reason if reason else 'None'
        reason = f"By {ctx.author.name}({ctx.author.id}) for: {audit_reason}"

        if member not in ctx.guild.members:
            msg = discord.Embed(
                title="Kick",
                description=f"{member.mention} is not in this server.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        if member == ctx.author:
            msg = discord.Embed(
                title="Kick",
                description=f"You can't kick yourself :O",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        await ctx.guild.kick(user=member, reason=reason)

        msg = discord.Embed(
            title="Kick",
            description=f"Kicked {member.mention}.",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Kick")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(
            name="Recipient",
            value=member.mention,
            inline=True)
        audit_msg.add_field(name="Reason", value=audit_reason, inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) kicked {member.name}({member.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["purge"]))
    @discord.option("amount",
                    type=int,
                    description="Amount of messages to purge. Default: 10",
                    default=10,
                    required=False)
    @discord.option("reason",
                    type=str,
                    description="Reason for purge.",
                    required=False)
    async def purge(
        self,
        ctx: discord.ApplicationContext,
        amount: int = 10
    ):

        """

        Purge messages. Default amount is 10.

        Args:
            amount (int|None): Amount of messages to purge.

        Returns:
            None

        """

        msgs = await ctx.channel.purge(limit=amount)

        msg = discord.Embed(
            title="Purge",
            description=f"Purged {len(msgs)} messages.",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Purge")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(
            name="# of Messages",
            value=len(msgs),
            inline=True)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) purged {len(msgs)} messages in {ctx.channel.name}({ctx.channel.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["mute"]))
    @discord.option("member",
                    type=discord.Member,
                    description="Member to mute.",
                    required=True)
    @discord.option("length",
                    type=str,
                    description="Length of mute. Default: 1m",
                    default="1m",
                    required=False)
    @discord.option("reason",
                    type=str,
                    description="Reason for mute.",
                    required=False)
    async def mute(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        length: str,
        reason: Union[str, None]
    ):

        """

        Mute a member. Default length is 1 minute.

        Args:
            member (discord.Member): Member to mute.
            length (str|None): Length of mute.
            reason (str|None): Reason for mute.

        Returns:
            None

        """

        # nonstandard bc it doesnt go into Discord's audit logs and shows up in
        # `/history <member>` instead
        reason = f"{ctx.author.mention} for: {reason if reason else 'None'}"

        mute_role = ctx.guild.get_role(mute_role_id)

        with open("db.json", "r") as f:
            data = json.load(f)
            mute_data = data["muteList"]

        if str(member.id) in mute_data:
            if mute_data[str(member.id)]["muted"]:
                msg = discord.Embed(
                    title="Mute",
                    description=f"{member.mention} is already muted. They have `{seconds_to_time_string(round(mute_data[str(member.id)]['muteEnd'] - time.time()))}` left.",
                    color=EMBED_COLOR,
                    timestamp=get_offset_time())
                msg.set_footer(
                    text=f"Requested by {ctx.author.name}",
                    icon_url=ctx.author.display_avatar)

                return await ctx.response.send_message(embed=msg)

        else:
            mute_data[str(member.id)] = {}
            mute_data[str(member.id)]["muteHistory"] = []

        mute_time = parse_time_string(length)

        if mute_time <= 0:
            msg = discord.Embed(
                title="Mute",
                description=f"Invalid mute time.\n\nFormat is: `<years>y<days>d<hours>h<minutes>m<seconds>s`\nExample: 1d3m = 1 day, 3 minutes",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        mute_data[str(member.id)]["muted"] = True
        mute_data[str(member.id)]["muteStart"] = time.time()
        mute_data[str(member.id)]["muteEnd"] = time.time() + mute_time
        mute_data[str(member.id)]["reason"] = reason

        data["muteList"] = mute_data

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

        await member.add_roles(mute_role, reason=reason)

        msg = discord.Embed(
            title="Mute",
            description=f"Muted {member.mention} for `{seconds_to_time_string(mute_time)}`. Their mute will end <t:{round(mute_data[str(member.id)]['muteEnd'])}:R>",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Mute")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=member.mention,
            inline=True)
        audit_msg.add_field(
            name="Recipient",
            value=member.mention,
            inline=True)
        audit_msg.add_field(
            name="Mute Start",
            value=f"<t:{round(mute_data[str(member.id)]['muteStart'])}:d>@<t:{round(mute_data[str(member.id)]['muteStart'])}:t>",
            inline=False)
        audit_msg.add_field(
            name="Mute End",
            value=f"<t:{round(mute_data[str(member.id)]['muteEnd'])}:d>@<t:{round(mute_data[str(member.id)]['muteEnd'])}:t>",
            inline=True)
        audit_msg.add_field(
            name="Mute Total",
            value=seconds_to_time_string(mute_time),
            inline=True)
        audit_msg.add_field(name="Reason", value=reason.split("> : ")[-1], inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) muted {member.name}({member.id}) for {seconds_to_time_string(mute_time)}.")
        
    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["mute"]))
    @discord.option("member",
                    type=discord.Member,
                    description="Member to unmute.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for unmute.",
                    required=False)
    async def unmute(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        reason: Union[str, None]
    ):
        
        """
        
        Unmute a member.

        Args:
            member (discord.Member): Member to unmute.
            reason (str|None): Reason for unmute.

        Returns:
            None
        
        """

        audit_reason = reason if reason else 'None'
        reason = f"By {ctx.author.name}({ctx.author.id}) for: {audit_reason}"

        mute_role = ctx.guild.get_role(mute_role_id)

        with open("db.json", "r") as f:
            data = json.load(f)
            mute_data = data["muteList"]

        if str(member.id) not in mute_data:
            msg = discord.Embed(
                title="Unmute",
                description=f"{member.mention} is not muted.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)

        if not mute_data[str(member.id)]["muted"]:
            msg = discord.Embed(
                title="Unmute",
                description=f"{member.mention} is not muted.",
                color=EMBED_COLOR,
                timestamp=get_offset_time())
            msg.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar)

            return await ctx.response.send_message(embed=msg)
        
        mute_data[str(member.id)]["muteHistory"].append({
            "muteStart": mute_data[str(member.id)]["muteStart"],
            "muteEnd": mute_data[str(member.id)]["muteEnd"],
            "reason": mute_data[str(member.id)]["reason"]})
        
        mute_data[str(member.id)]["muted"] = False
        mute_data[str(member.id)]["muteStart"] = -1
        mute_data[str(member.id)]["muteEnd"] = -1
        mute_data[str(member.id)]["reason"] = ""

        data["muteList"] = mute_data

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

        await member.remove_roles(mute_role, reason=reason)

        msg = discord.Embed(
            title="Unmute",
            description=f"Unmuted {member.mention}.",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        
        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Unmute")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(
            name="Recipient",
            value=member.mention,
            inline=True)
        audit_msg.add_field(name="Reason", value=audit_reason, inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)
        
        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) unmuted {member.name}({member.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["warn"]))
    @discord.option("member",
                    type=discord.Member,
                    description="Member to warn.",
                    required=True)
    @discord.option("reason",
                    type=str,
                    description="Reason for warn.",
                    required=False)
    async def warn(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        reason: Union[str, None]
    ):

        """

        Warn a member.

        Args:
            member (discord.Member): Member to warn.
            reason (str|None): Reason for warn.

        Returns:
            None

        """

        reason = f"{ctx.author.mention} for: {reason if reason else 'None'}"

        with open("db.json", "r") as f:
            data = json.load(f)
            warn_data = data["warnList"]

        if str(member.id) not in warn_data:
            warn_data[str(member.id)] = {}
            warn_data[str(member.id)]["warns"] = []

        warn_data[str(member.id)]["warns"].append({
            "reason": reason,
            "time": time.time()
        })

        data["warnList"] = warn_data

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

        msg = discord.Embed(
            title="Warn",
            description=f"Warned {member.mention}",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

        response_msg = (await ctx.channel.history(limit=1).flatten())[0]

        audit_msg = Embed(
            title="Link to action",
            url=response_msg.jump_url,
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        audit_msg.set_author(name=f"Moderation - Warn")
        audit_msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)
        audit_msg.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=True)
        audit_msg.add_field(
            name="Recipient",
            value=member.mention,
            inline=True)
        audit_msg.add_field(name="Reason", value=reason.split("> : ")[-1], inline=False)
        audit_msg.add_field(
            name="Timestamp",
            value=f"`{get_offset_time().isoformat()}`",
            inline=False)

        await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)

        log("moderation", __name__,
            f"{ctx.author.name}({ctx.author.id}) warned {member.name}({member.id}).")

    @commands.slash_command(guild_ids=guild_list)
    @commands.check_any(commands.is_owner(),
                        commands.has_any_role(*permissionList["warn"]))
    @discord.option("member",
                    type=discord.Member,
                    description="Member to view moderation history of.",
                    required=True)
    async def history(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member
    ):
        with open("db.json", "r") as f:
            data = json.load(f)
            warn_data = data["warnList"]
            mute_data = data["muteList"]

        if str(member.id) not in warn_data:
            warn_data[str(member.id)] = {}
            warn_data[str(member.id)]["warns"] = []

        if str(member.id) not in mute_data:
            mute_data[str(member.id)] = {}
            mute_data[str(member.id)]["muteHistory"] = []

        msg = discord.Embed(
            title="Moderation History",
            description=f"History for {member.mention}",
            color=EMBED_COLOR,
            timestamp=get_offset_time())
        msg.set_thumbnail(url=member.display_avatar)

        if len(warn_data[str(member.id)]["warns"]) > 0:
            msg.add_field(name="Warns", value="\n".join(
                [f"{warn['reason']}\n<t:{round(warn['time'])}:R>" for warn in warn_data[str(member.id)]["warns"]]), inline=False)
        else:
            msg.add_field(name="Warns", value="N/A", inline=False)

        if len(mute_data[str(member.id)]["muteHistory"]) > 0:
            msg.add_field(name="Mutes", value="\n".join(
                [f"{mute['reason']}\nEnded <t:{round(mute['muteEnd'])}:R>" for mute in mute_data[str(member.id)]["muteHistory"]]), inline=False)
        else:
            msg.add_field(name="Mutes", value="N/A", inline=False)

        msg.add_field(
            name="Kicks / Bans",
            value="*Kicks and Bans are not currently tracked*",
            inline=False)
        
        msg.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar)

        await ctx.response.send_message(embed=msg)

    @tasks.loop(seconds=5)
    async def unmute_loop(self):

        with open("db.json", "r") as f:
            data = json.load(f)
            audit_channel_id = data["options"]["auditChannelId"]
            mute_data = data["muteList"]

        for member_id in mute_data:
            if mute_data[member_id]["muted"]:
                if mute_data[member_id]["muteEnd"] <= time.time():

                    # If more than one guild is added, this will need to be
                    # changed
                    guild = self.bot.get_guild(int(guild_list[0]))

                    mute_role = guild.get_role(mute_role_id)
                    member = guild.get_member(int(member_id))

                    await member.remove_roles(mute_role, reason="Mute ended.")

                    mute_data[member_id]["muteHistory"].append({
                        "muteStart": mute_data[member_id]["muteStart"],
                        "muteEnd": mute_data[member_id]["muteEnd"],
                        "reason": mute_data[member_id]["reason"]})

                    audit_msg = Embed(
                        color=EMBED_COLOR, timestamp=get_offset_time())
                    audit_msg.set_author(name=f"Automoderation - Unmute")
                    audit_msg.add_field(
                        name="Recipient",
                        value=f"{member.mention}",
                        inline=True)
                    audit_msg.add_field(
                        name="Mute Start",
                        value=f"<t:{round(mute_data[str(member.id)]['muteStart'])}:d>@<t:{round(mute_data[str(member.id)]['muteStart'])}:t>",
                        inline=False)
                    audit_msg.add_field(
                        name="Mute End",
                        value=f"<t:{round(mute_data[str(member.id)]['muteEnd'])}:d>@<t:{round(mute_data[str(member.id)]['muteEnd'])}:t>",
                        inline=True)
                    audit_msg.add_field(name="Mute Total", value=seconds_to_time_string(mute_data[str(
                        member.id)]['muteEnd'] - mute_data[str(member.id)]['muteStart']), inline=True)
                    audit_msg.add_field(
                        name="Reason",
                        value=mute_data[member_id]["reason"].split("> : ")[-1],
                        inline=False)
                    audit_msg.add_field(
                        name="Timestamp",
                        value=f"`{get_offset_time().isoformat()}`",
                        inline=False)

                    await self.bot.get_channel(audit_channel_id).send(embed=audit_msg)
                    log("moderation", __name__,
                        f"{member.name}({member.id}) was unmuted automatically.")

                    mute_data[member_id]["muted"] = False
                    mute_data[member_id]["muteStart"] = -1
                    mute_data[member_id]["muteEnd"] = -1
                    mute_data[member_id]["reason"] = ""

        data["muteList"] = mute_data

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

    @unmute_loop.before_loop
    async def before_unban_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, discord.ApplicationCommandInvokeError):
            await ctx.response.send_message(content=f"Whatever you just tried to do, I couldn't do it.\nDM <@!322903939140026379> with a screenshot and description of what you were trying to do.", ephemeral=True)


def setup(bot):
    log("trace", __name__, f"Loading {os.path.basename(__file__)} cog.")
    try:
        bot.add_cog(Moderation(bot))
        log("debug", __name__, f"Loaded {os.path.basename(__file__)} cog.")
    except Exception as e:
        log("error", __name__,
            f"Failed to load {os.path.basename(__file__)} cog.")


def teardown(bot):
    log("trace", __name__, f"Unloading {os.path.basename(__file__)} cog.")
    try:
        bot.remove_cog(Moderation(bot))
        log("debug", __name__, f"Unloaded {os.path.basename(__file__)} cog.")
    except Exception as e:
        log("error", __name__,
            f"Failed to unload {os.path.basename(__file__)} cog.")
