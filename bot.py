from pathlib import Path

import discord
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        self.prefix = "!"
        super().__init__(command_prefix = self.prefix, case_insensitive = True, intents = discord.Intents.all())

    async def setup_hook(self):
        import os
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cog_name = f"cogs.{filename[:-3]}"
                print(f"loading {cog_name}")
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        self.client_id = (await self.application_info()).id
        print("Bot is ready")
