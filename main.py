# This will be used later for email verification
# import os
# import dotenv
# from sendEmail import EmailSender

# dotenv.load_dotenv()

# emailSender = EmailSender(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))

# emailSender.sendEmail(receiver="pete@purdue.edu", message_body="""
# Please respond to the bot with ___ to verify your email.
# """)

import dotenv
import os
import discord
from discord.ext import commands

# Ensure that working dir is the same as the file dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv()

bot = commands.Bot()
guild_list = os.getenv('GUILD_LIST').split(',')

@bot.event
async def on_ready():
    print(f'[INFO] {bot.user} has successfully connected.')

@bot.slash_command(guild_ids=guild_list)
async def verify(ctx: discord.ApplicationContext):
    # email regex: ^[a-z0-9]+@purdue\.edu$
    pass

bot.run(os.getenv('BOT_TOKEN'))