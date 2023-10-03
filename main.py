import dotenv
import json
import os
import discord
from discord.ext import commands
from discord import Option
from modal import VerificationModal

# Ensure that working dir is the same as the file dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()

bot = commands.Bot()
guild_list = os.getenv('GUILD_LIST').split(',')



# @TODO: add detection for disconnect (MONITORING); add disconnect to log (LOGGING)
@bot.event
async def on_ready():
    # @TODO: add ready to log (LOGGING)
    print(f'[INFO] {bot.user} has successfully connected.')

@bot.slash_command(guild_ids=guild_list)
async def verify(
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
        with open("db.json") as f:
            data = json.load(f)

        if str(ctx.author.id) not in data['emailVerification']:
            return await ctx.response.send_message(content=f"You are not verified. Please do `/verify` to start the verification process.", ephemeral=True)
        
        if data["emailVerification"][str(ctx.author.id)]["verified"]:
            return await ctx.response.send_message(content=f"You are already verified.", ephemeral=True)
        
        if data["emailVerification"][str(ctx.author.id)]["verificationCode"] != int(verification_code):
            return await ctx.response.send_message(content=f"Invalid verification code.", ephemeral=True)
        
        data["emailVerification"][str(ctx.author.id)]["verified"] = True

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

        # Do any additional logic here

        await ctx.response.send_message(content=f"Welcome to ARC! You are now verified.")

bot.run(os.getenv('BOT_TOKEN'))