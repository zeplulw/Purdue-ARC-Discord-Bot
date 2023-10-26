import dotenv
import json
import os
import discord
import datetime
from discord.ext import commands
from discord import Option
from modal import VerificationModal
from logger import Logger
from main import guild_list

dotenv.load_dotenv()
log = Logger().log


def getCurrentTime() -> str:
    return datetime.datetime.now().isoformat()


class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=guild_list)
    @discord.option("verification_code",
                    type=str,
                    description="Verification code recieved in email.",
                    min_length=6,
                    max_length=6,
                    required=False)
    async def verify(
        self,
        ctx: discord.ApplicationContext,
        verification_code: str
    ):

        if not verification_code:
            await ctx.response.send_modal(VerificationModal())

        else:
            with open("db.json") as f:
                data = json.load(f)

            if str(ctx.author.id) not in data['emailVerification']:
                return await ctx.response.send_message(content=f"You are not verified. Please do `/verify` to start the verification process.", ephemeral=True)

            if data["emailVerification"][str(ctx.author.id)]["verified"]:
                return await ctx.response.send_message(content=f"You are already verified.", ephemeral=True)

            if data["emailVerification"][str(
                    ctx.author.id)]["verificationCode"] != int(verification_code):
                return await ctx.response.send_message(content=f"Invalid verification code.", ephemeral=True)

            data["emailVerification"][str(ctx.author.id)]["verified"] = True

            with open("db.json", "w") as f:
                json.dump(data, f, indent=4)

            # Do any additional logic here

            await ctx.response.send_message(content=f"Welcome to ARC! You are now verified.")


def setup(bot):
    log("trace", __name__, f"Loading {os.path.basename(__file__)} cog.")
    try:
        bot.add_cog(Verification(bot))
        log("debug", __name__, f"Loaded {os.path.basename(__file__)} cog.")
    except Exception as e:
        log("error", __name__,
            f"Failed to load {os.path.basename(__file__)} cog.")


def teardown(bot):
    log("trace", __name__, f"Unloading {os.path.basename(__file__)} cog.")
    try:
        bot.remove_cog(Verification(bot))
        log("debug", __name__, f"Unloaded {os.path.basename(__file__)} cog.")
    except Exception as e:
        log("error", __name__,
            f"Failed to unload {os.path.basename(__file__)} cog.")
