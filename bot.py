"""
CONTAINS AI-GENERATED CONTENT

Commands:
  /trout [target]         - whacks target (or you) with a wet trout, subject to a per-user cooldown
  /trout-cooldown <secs>  - (Administrator permission required) changes the cooldown length for everyone

Setup steps are in README.md.
"""

import json
import os
import time

import discord
from discord import app_commands
from discord.ext import commands

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# Put your bot token in an environment variable instead of typing it directly
# into this file. That way you can post this code publicly without leaking
# your token. See README.md for how to set this.
TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# URL of the trout image. Easiest option: upload the image to any channel in
# your server once, right-click it, "Copy Link", and paste that link here.
TROUT_IMAGE_URL = "https://github.com/some-amoeba/troutbot/blob/main/trout.png?raw=true"

CONFIG_FILE = "config.json"


def load_cooldown_seconds() -> int:
    """Read the cooldown length (in seconds) from config.json."""
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    return data["cooldown_seconds"]


def save_cooldown_seconds(seconds: int) -> None:
    """Write a new cooldown length to config.json so it survives restarts."""
    with open(CONFIG_FILE, "w") as f:
        json.dump({"cooldown_seconds": seconds}, f)


# ---------------------------------------------------------------------------
# BOT SETUP
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)  # prefix is unused since we use slash commands

# In-memory record of when each user last used /trout.
# Structure: {user_id: unix_timestamp_of_last_use}
# This resets if the bot restarts -- that's fine, it just means everyone's
# cooldown clears on restart, which is a reasonable default.
last_used: dict[int, float] = {}

# Loaded once at startup, updated whenever /trout-cooldown is run.
cooldown_seconds: int = load_cooldown_seconds()


@bot.event
async def on_ready():
    # This syncs your slash commands with Discord. Only needs to run once
    # per code change, but it's cheap to run every startup.
    await bot.tree.sync()
    print(f"Logged in as {bot.user}. Cooldown is currently {cooldown_seconds}s.")


# ---------------------------------------------------------------------------
# /trout COMMAND
# ---------------------------------------------------------------------------

@bot.tree.command(name="trout", description="Whack someone with a wet trout")
@app_commands.describe(target="Who to whack (optional -- leave blank to whack yourself)")
async def trout(interaction: discord.Interaction, target: discord.Member | None = None):
    user_id = interaction.user.id
    now = time.time()

    # --- Cooldown check ---
    last_time = last_used.get(user_id)
    if last_time is not None:
        elapsed = now - last_time
        if elapsed < cooldown_seconds:
            remaining = round(cooldown_seconds - elapsed)
            # ephemeral=True means only the person who ran the command sees this message
            await interaction.response.send_message(
                f"You're on cooldown. Try again in {remaining}s.",
                ephemeral=True,
            )
            return

    # Passed the cooldown check -- record this use.
    last_used[user_id] = now

    # --- Build the response ---
    embed = discord.Embed(title="Whack!", description="You've been whacked with a wet trout!")
    embed.set_image(url=TROUT_IMAGE_URL)

    # Optional tagging: if a target was given, mention them above the embed.
    content = target.mention if target else None

    await interaction.response.send_message(content=content, embed=embed)


# ---------------------------------------------------------------------------
# /trout-cooldown COMMAND (admin-only)
# ---------------------------------------------------------------------------

@bot.tree.command(name="trout-cooldown", description="Set the trout cooldown (in seconds) for everyone")
@app_commands.describe(seconds="New cooldown length in seconds")
@app_commands.checks.has_permissions(administrator=True)
async def trout_cooldown(interaction: discord.Interaction, seconds: int):
    global cooldown_seconds

    if seconds < 0:
        await interaction.response.send_message("Cooldown can't be negative.", ephemeral=True)
        return

    cooldown_seconds = seconds
    save_cooldown_seconds(seconds)
    await interaction.response.send_message(f"Trout cooldown set to {seconds}s.", ephemeral=True)


@trout_cooldown.error
async def trout_cooldown_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You need the 'Administrator' permission to change the cooldown.",
            ephemeral=True,
        )
    else:
        raise error


# ---------------------------------------------------------------------------
bot.run(TOKEN)
