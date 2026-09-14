import os
import discord
from discord.ext import commands
from bot.views.main_menu import MainMenuView, build_main_embed

class DayZStoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Register persistent views so buttons work even after restart
        self.add_view(MainMenuView())
        print("✓ Visões persistentes do Bot registradas!")

    async def on_ready(self):
        print(f"✓ Bot conectado como {self.user} (ID: {self.user.id})")

def setup_bot_channel_message():
    """Utility function to create or build the main store panel embed and view."""
    view = MainMenuView()
    embed = build_main_embed("DayZ Store")
    return embed, view
