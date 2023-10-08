import dotenv
import json
import os
import discord
import datetime
from discord import Embed
from discord.ext import commands
from discord import Option
from modal import VerificationModal

# Ensure that working dir is the same as the file dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()

bot = commands.Bot()
guild_list = os.getenv('GUILD_LIST').split(',')
EMBED_COLOR = hex(int(os.getenv('EMBED_COLOR'), 16))
ARC_ICON_URL = os.getenv('ARC_ICON_URL')

# @TODO: add detection for disconnect (MONITORING); add disconnect to log (LOGGING)
@bot.event
async def on_ready():
    # @TODO: add ready to log (LOGGING)
    print(f'[INFO] {bot.user} has successfully connected.')

@bot.slash_command(guild_ids=guild_list)
async def load(ctx: discord.ApplicationContext, extension: Option(str, description="Extension to load.")):

    """
    Load a cog.

    Args:
        extension (str): The extension to load.

    Returns:
        None
    """

    bot.load_extension(f'cogs.{extension}')
    await ctx.response.send_message(content=f'Loaded {extension}.')

@bot.slash_command(guild_ids=guild_list)
async def unload(ctx: discord.ApplicationContext, extension: Option(str, description="Extension to unload.")):

    """
    Unloads a cog.

    Args:
        extension (str): The extension to unload.

    Returns:
        None
    """

    bot.unload_extension(f'cogs.{extension}')
    await ctx.response.send_message(content=f'Unloaded {extension}.')

@bot.slash_command(guild_ids=guild_list)
async def reload(ctx: discord.ApplicationContext, extension: Option(str, description="Extension to reload.")):

    """
    Reloads a cog. Equal to unload and load.

    Args:
        extension (str): The extension to reload.

    Returns:
        None
    """

    bot.reload_extension(f'cogs.{extension}')
    await ctx.response.send_message(content=f'Reloaded {extension}.')

@bot.slash_command(guild_ids=guild_list)
async def reloadall(ctx: discord.ApplicationContext):

    """
    Reloads all cogs.

    Args:
        None

    Returns:
        None
    """

    cog_status = {}
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):

            cog_status[filename[:-3]] = None

            try:
                bot.unload_extension(f'cogs.{filename[:-3]}')
                cog_status[filename[:-3]] = f'`[SUCCESS] {filename[:-3]}: Unloaded`'
            except Exception as e:
                cog_status[filename[:-3]] = f'`[ERROR] {filename[:-3]}: {type(e)}`'

            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                cog_status[filename[:-3]] = f'`[SUCCESS] {filename[:-3]}: Loaded`'
            except Exception as e:
                cog_status[filename[:-3]] = f'`[ERROR] {filename[:-3]}: {type(e)}`'

    msg = Embed(title=f"Reload All Cogs", color=EMBED_COLOR, timestamp=datetime.datetime)
    msg.set_author(name="ARC Assistant", icon_url=ARC_ICON_URL)
    msg.description = "\n".join((f'{cog}: {cog_status[cog]}' for cog in cog_status))
    msg.set_footer(text=f"Requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)

    await ctx.response.send_message(embed=msg)

# Logging takes place in individual cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv('BOT_TOKEN'))