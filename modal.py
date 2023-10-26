import discord
import asyncio
import json
import os
import random
import requests
import re
from discord.utils import get
from discord.ext import commands
from discord.ui import InputText, Modal, Button, View
from sendEmail import EmailSender


class VerificationModal(Modal):

    """
    Shows a modal to the user to verify their Purdue email.

    """

    def __init__(self) -> None:
        super().__init__(title="ARC Email Verification")
        self.add_item(
            InputText(
                label="Purdue Email",
                placeholder="pete@purdue.edu",
                style=discord.InputTextStyle.short,
            )
        )

        self.email_sender = EmailSender(
            os.getenv('EMAIL_ADDRESS'),
            os.getenv('EMAIL_PASSWORD'))

    async def callback(self, interaction: discord.Interaction):

        if not re.match("^[a-z0-9]+@purdue\\.edu$", self.children[0].value):
            return await interaction.response.send_message(content=f"Please enter a valid Purdue email.", ephemeral=True)

        with open("db.json") as f:
            data = json.load(f)

        if str(interaction.user.id) in data['emailVerification']:
            return await interaction.response.send_message(content=f"You are already verified.", ephemeral=True)

        await interaction.response.send_message(content="Please wait.", ephemeral=True)

        response = requests.request(
            "POST",
            "https://www.purdue.edu/directory/Advanced",
            params={
                "SearchString": self.children[0].value,
                "SelectedSearchTypeId": "0",
                "UsingParam": "Search by Email",
                "CampusParam": "All Campuses",
                "DepartmentParam": "All Departments",
                "SchoolParam": "All Schools"})

        if response.text.find(f"mailto:{self.children[0].value}") == -1:
            return await interaction.edit_original_response(content=f"Email does not exist within Purdue's directory.")

        _verification_code = random.randint(100000, 999999)
        self.email_sender.send_verification_email(
            username=interaction.user.name,
            receiver=self.children[0].value,
            verification_code=_verification_code)

        data["emailVerification"][str(interaction.user.id)] = {
            "email": self.children[0].value, "verified": False, "verificationCode": _verification_code}

        with open("db.json", "w") as f:
            json.dump(data, f, indent=4)

        await interaction.edit_original_response(content=f"Please check your email for a verification code and instructions. If you do not see an email from `admin@benlima.dev`, please check your spam folder")
