import dotenv
import os
import discord
import datetime
import atexit
from discord import Embed
from discord.ext import commands
from discord import Option
from logger import log

# Ensure that working dir is the same as the file dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()

bot = commands.Bot(intents=discord.Intents.all())
guild_list = os.getenv('GUILD_LIST').split(',')
EMBED_COLOR = int(os.getenv('EMBED_COLOR'), 16)
ARC_ICON_URL = os.getenv('ARC_ICON_URL')

# @TODO: add detection for disconnect (MONITORING); add disconnect to log (LOGGING)
@bot.event
async def on_ready():
    # @TODO: add ready to log (LOGGING)
    log("info", __name__, f"{bot.user} has logged in and is connected to Discord.")

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
    log("debug", __name__, f"{ctx.author.name} loaded {extension}.")

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
    log("debug", __name__, f"{ctx.author.name} unloaded {extension}.")

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
    log("debug", __name__, f"{ctx.author.name} reloaded {extension}.")

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

            cog_name = filename[:-3]
            cog_status[cog_name] = None

            try:
                bot.unload_extension(f'cogs.{cog_name}')
                cog_status[cog_name] = f'`[SUCCESS] {cog_name}: Unloaded`'
            except Exception as e:
                cog_status[cog_name] = f'`[ERROR] {cog_name}: {type(e)}`'

            try:
                bot.load_extension(f'cogs.{cog_name}')
                cog_status[cog_name] = f'`[SUCCESS] {cog_name}: Loaded`'
            except Exception as e:
                cog_status[cog_name] = f'`[ERROR] {cog_name}: {type(e)}`'

    msg = Embed(title=f"Reload All Cogs", color=EMBED_COLOR, timestamp=datetime.datetime.utcnow())
    msg.set_author(name="ARC Assistant", icon_url=ARC_ICON_URL)
    msg.description = "\n".join((f'{cog}: {cog_status[cog]}' for cog in cog_status))
    msg.set_footer(text=f"Requested by: {ctx.author.name}", icon_url=ctx.author.display_avatar)

    await ctx.response.send_message(embed=msg)
    log("debug", __name__, f"{ctx.author.name} reloaded all cogs.")

@bot.event
async def on_error(ctx, error):
    pass

# Logging takes place in individual cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

def atExitHandler():
    log("fatal", __name__, "sum ting wong")

atexit.register(atExitHandler)

bot.run(os.getenv('BOT_TOKEN'))