import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio


# Load environment variables
load_dotenv()

# Get token and channel ID from the .env file
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True  # To read messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Remove default help command
bot.remove_command('help')

# Curator command group
@bot.group(invoke_without_command=True)
async def curator(ctx):
    await ctx.send("Use `!curator add` to start submitting your theme or `!curator help` to get more information.")

# Custom Help Command for curator (subcommand)
@curator.command()
async def help(ctx):
    help_text = """
    **Commands available under !curator:**

    `!curator add` - Start the theme submission process. The bot will ask you a series of questions.

    `!curator delete <message_id>` - Delete your theme submission by its message ID. Only the user who submitted the theme can delete it.
    """
    await ctx.send(help_text)

@curator.command()
async def add(ctx):
    await ctx.send("Let's submit your theme! I'll ask you a few questions. You can type 'cancel' at any time to quit.")
    
    def check(message):
        return message.author == ctx.author and isinstance(message.channel, (discord.TextChannel, discord.DMChannel))

    try:
        # Step 1: Ask for the theme name
        await ctx.send("What is the name of your theme? (Type 'cancel' to cancel the process)")
        theme_name_message = await bot.wait_for('message', check=check, timeout=60.0)
        
        # Check if the user wants to cancel the process
        if theme_name_message.content.lower() == 'cancel':
            await ctx.send("Theme submission has been canceled.")
            return

        theme_name = theme_name_message.content

        # Step 2: Ask for the theme description
        await ctx.send("Please provide a description for your theme. (Type 'cancel' to cancel the process)")
        theme_description_message = await bot.wait_for('message', check=check, timeout=60.0)

        # Check if the user wants to cancel the process
        if theme_description_message.content.lower() == 'cancel':
            await ctx.send("Theme submission has been canceled.")
            return

        theme_description = theme_description_message.content

        # Step 3: Ask for the theme link
        await ctx.send("Please provide a link for your theme (e.g., to GitHub or a preview). (Type 'cancel' to cancel the process)")
        theme_link_message = await bot.wait_for('message', check=check, timeout=60.0)

        # Check if the user wants to cancel the process
        if theme_link_message.content.lower() == 'cancel':
            await ctx.send("Theme submission has been canceled.")
            return

        theme_link = theme_link_message.content

        # Send the theme information as a plain text message
        theme_submission_message = f"**Submitted by:** <@{ctx.author.id}>\n**Name:** {theme_name}\n**Description:** {theme_description}\n {theme_link}"
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(theme_submission_message)
        
        # Acknowledge the submission to the user
        await ctx.send("Your theme has been submitted successfully!")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please try again later.")

@curator.command()
async def delete(ctx, message_id: int = None):
    if message_id is None:
        # Prompt the user to provide the message ID
        await ctx.send("Please provide the message ID of the theme submission you wish to delete.")
        return

    # Fetch the channel by ID
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await ctx.send("Channel not found.")
        return
    
    try:
        # Fetch the message by ID within the correct channel
        message = await channel.fetch_message(message_id)

        # Check if the user's ID exists in the "Submitted by:" part of the message
        if f"<@{ctx.author.id}>" in message.content:
            await message.delete()
            await ctx.send("Your theme submission has been deleted successfully!")
        else:
            await ctx.send("You can only delete your own submissions.")
    except discord.NotFound:
        await ctx.send("Could not find the message with that ID.")
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete this message.")

# Run the bot
bot.run(TOKEN)
