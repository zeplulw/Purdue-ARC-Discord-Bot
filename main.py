import dotenv
import os
import discord
import datetime
import atexit
import json
from discord import Embed
from discord.ext import commands
from discord import Option
from logger import Logger

# Ensure that working dir is the same as the file dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()
log = Logger().log

bot = commands.Bot(intents=discord.Intents.all())

with open("db.json", "r") as f:
    options = json.load(f)["options"]
    permissionList = options["permissionList"]
    guild_list = options["guildList"]
    EMBED_COLOR = int(options["embedColor"], 16)
    ARC_ICON_URL = options["arcIconURL"]

cog_list = [filename[:-3] for filename in os.listdir('./cogs') if filename.endswith('.py')]

# @TODO: add detection for disconnect (i dont think this is possible with stock py-cord) (MONITORING); add disconnect to log (LOGGING)
@bot.event
async def on_ready():
    log("info", __name__, f"{bot.user} has logged in and is connected to Discord.", important=True)

@bot.slash_command(guild_ids=guild_list)
@commands.check_any(commands.is_owner(), commands.has_any_role(*permissionList["reload"]))
@discord.option("extension", type=str, description="Extension to load.", choices=cog_list, required=True)
async def load(
        ctx: discord.ApplicationContext,
        extension: str
    ):

    """
    Load a cog.

    Args:
        extension (str): The extension to load.

    Returns:
        None
    """

    # TODO: add check for if cog is already loaded (GLOBAL ERROR HANDLER)
    bot.load_extension(f'cogs.{extension}')
    await ctx.response.send_message(content=f'Loaded {extension}.')
    log("debug", __name__, f"{ctx.author.name} loaded {extension}.")

@bot.slash_command(guild_ids=guild_list)
@commands.check_any(commands.is_owner(), commands.has_any_role(*permissionList["reload"]))
@discord.option("extension", type=str, description="Extension to unload.", choices=cog_list, required=True)
async def unload(
        ctx: discord.ApplicationContext,
        extension: str
    ):

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
@commands.check_any(commands.has_any_role(*permissionList["reload"]))
@discord.option("extension", type=str, description="Extension to reload.", choices=cog_list, required=True)
async def reload(
        ctx: discord.ApplicationContext,
        extension: str
    ):

    """
    Reloads a cog. Equal to unload and load.

    Args:
        extension (str): The extension to reload.

    Returns:
        None
    """

    bot.reload_extension(f'cogs.{extension}')
    await ctx.response.send_message(content=f'Reloaded {extension}.')
    log("info", __name__, f"{ctx.author.name} reloaded {extension}.")

@bot.slash_command(guild_ids=guild_list)
@commands.check_any(commands.is_owner(), commands.has_any_role(*permissionList["reload"]))
async def reloadall(ctx: discord.ApplicationContext):

    """
    Reloads all cogs.

    Args:
        None

    Returns:
        None
    """

    cog_status = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):

            cog_name = filename[:-3]

            try:
                bot.reload_extension(f'cogs.{cog_name}')
                cog_status.append(f"`{cog_name}: ✅`")
            except Exception as e:
                cog_status.append(f"`{cog_name}: ❌ (see log)`")
                log("error", __name__, f"Failed to reload {cog_name}: {e}")

    msg = Embed(title=f"Reload All Cogs", color=EMBED_COLOR, timestamp=datetime.datetime.utcnow())
    msg.set_author(name="ARC Assistant", icon_url=ARC_ICON_URL)
    msg.description = "\n".join(cog_status)
    msg.set_footer(text=f"Requested by: {ctx.author.name}", icon_url=ctx.author.display_avatar)

    await ctx.response.send_message(embed=msg)
    log("info", __name__, f"{ctx.author.name} reloaded all cogs.")

# Logging of cog loading takes place in individual cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

@atexit.register
def atExitHandler():
    log("info", __name__, "Bot exited.", important=True)

bot.run(os.getenv('BOT_TOKEN'))