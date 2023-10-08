import dotenv
import json
import os
import discord
from discord.ext import commands
from discord import Option
from modal import VerificationModal

dotenv.load_dotenv()

guild_list = os.getenv('GUILD_LIST').split(',')

class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=guild_list)
    async def verify(
        self,
        ctx: discord.ApplicationContext,
        verification_code: Option(
            str,
            description="Verification code recieved in email.",
            min_length=6,
            max_length=6,
            required=False)):
        
        if not verification_code:
            await ctx.response.send_modal(VerificationModal())

        else:
            with open("../db.json") as f:
                data = json.load(f)

            print(ctx, type(ctx))

            if str(ctx.author.id) not in data['emailVerification']:
                return await ctx.response.send_message(content=f"You are not verified. Please do `/verify` to start the verification process.", ephemeral=True)
            
            if data["emailVerification"][str(ctx.author.id)]["verified"]:
                return await ctx.response.send_message(content=f"You are already verified.", ephemeral=True)
            
            if data["emailVerification"][str(ctx.author.id)]["verificationCode"] != int(verification_code):
                return await ctx.response.send_message(content=f"Invalid verification code.", ephemeral=True)
            
            data["emailVerification"][str(ctx.author.id)]["verified"] = True

            with open("../db.json", "w") as f:
                json.dump(data, f, indent=4)

            # Do any additional logic here

            await ctx.response.send_message(content=f"Welcome to ARC! You are now verified.")

def setup(bot):
    print(f"[INFO] Loading {os.path.basename(__file__)} cog.")
    bot.add_cog(Verification(bot))
    print(f"[INFO] Loaded {os.path.basename(__file__)} cog.")


def teardown(bot):
    print(f"[INFO] Unloading {os.path.basename(__file__)} cog.")
    bot.remove_cog(Verification(bot))
    print(f"[INFO] Unloaded {os.path.basename(__file__)} cog.")