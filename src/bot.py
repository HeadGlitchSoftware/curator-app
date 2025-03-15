import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import re

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Remove default help command
bot.remove_command('help')

# Validation functions
def is_valid_hex_name(name):
    """Validates that the theme name is an 8-character long hexadecimal string."""
    return bool(re.fullmatch(r"^[0-9a-f]{8}$", name))

def is_valid_image(attachments):
    """Check if the message contains an image attachment."""
    if len(attachments) == 0:
        return False
    image_attachment = attachments[0]
    return image_attachment.content_type.startswith("image/")  # Check if the attachment is an image

# Error messages mapped automatically by validation function
INPUT_ERRORS = {
    is_valid_hex_name: "Invalid name! It must be a hex value exactly 8 characters long.",
    is_valid_image: "Invalid image! Please upload an image file.",
}

async def prompt_user(ctx, question, validation_func=None, timeout=300.0):
    """Helper function to ask a user a question, validate input, and allow 'back'."""
    while True:
        await ctx.send(question)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            response = await bot.wait_for("message", check=check, timeout=timeout)
            user_input = response.content.strip()

            if user_input.lower() in ["cancel", "back"]:
                return user_input

            # Check for color-code validation
            if validation_func == is_valid_hex_name and not validation_func(user_input):
                error_message = INPUT_ERRORS.get(validation_func, "Invalid input. Please follow the format requirements.")
                await ctx.send(error_message)
                continue  # Ask again if input is invalid

            # Check for image validation
            if validation_func == is_valid_image and not validation_func(response.attachments):
                error_message = INPUT_ERRORS.get(validation_func, "Invalid input. Please follow the format requirements.")
                await ctx.send(error_message)
                continue  # Ask again if input is invalid

            return response  # Valid input

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try again later.")
            return None

def format_submission(author_id, *answers):
    """Formats the theme submission message with dynamic arguments."""
    # Combine the answers with their respective tags in a readable format
    formatted_answers = "\n".join([f"**{tag}:** {answer}" for tag, answer in answers])
    
    # Return the formatted string
    return f"**Submitted by:** <@{author_id}>\n{formatted_answers}"

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

# List of questions with their validation functions and associated tags
questions = [
    {"tag": "Theme Name",                   "question": "What is the name of your theme?",                              "validation": None},
    {"tag": "Font",                         "question": "What is the font used in this theme?",                         "validation": None},
    {"tag": "Background Color",             "question": "Enter the \"Background Color\" of your theme.",                "validation": is_valid_hex_name},
    {"tag": "Input Color",                  "question": "Enter the \"Input Color\" of your theme.",                     "validation": is_valid_hex_name},
    {"tag": "Command Color",                "question": "Enter the \"Command Color\" of your theme.",                   "validation": is_valid_hex_name},
    {"tag": "Normal Text & Arrow Color",    "question": "Enter the \"Normal Text & Arrow Color\" of your theme.",       "validation": is_valid_hex_name},
    {"tag": "Error Text Color",             "question": "Enter the \"Error Text Color\" of your theme.",                "validation": is_valid_hex_name},
    {"tag": "Positive Text Color",          "question": "Enter the \"Positive Text Color\" of your theme.",             "validation": is_valid_hex_name},
    {"tag": "Warning Text Color",           "question": "Enter the \"Warning Text Color\" of your theme.",              "validation": is_valid_hex_name},
    {"tag": "Suggestions Color",            "question": "Enter the \"Suggestions Color\" of your theme.",               "validation": is_valid_hex_name},
    {"tag": "Suggestion Bar Color",         "question": "Enter the \"Suggestion Bar Color\" of your theme.",            "validation": is_valid_hex_name},
    {"tag": "Preview",                      "question": "Please upload a preview image of your theme.",                 "validation": is_valid_image},
    {"tag": "Background",                   "question": "Please upload the background image used for your theme.",      "validation": is_valid_image},
]

@curator.command()
async def add(ctx):
    """Guides the user through the theme submission process with validation and 'back' support."""
    await ctx.send(
        "Let's submit your theme! You can type 'cancel' to quit or 'back' to go to the previous question.\n\n"
    )
    
    answers = []  # List to store question-answer pairs
    current_index = 0

    while current_index < len(questions):
        question = questions[current_index]["question"]
        validation_func = questions[current_index]["validation"]
        
        # Ask the user the current question
        answer = await prompt_user(ctx, question, validation_func)

        if answer is None or answer == "cancel":
            await ctx.send("Theme submission has been canceled.")
            return
        
        if answer == "back":
            if current_index > 0:
                current_index -= 1  # Go back to the previous question
                continue
            else:
                await ctx.send("You're already at the first question.")
                continue

        # Handle image-based validation functions
        if validation_func == is_valid_image and answer.attachments:
            # Get the image URL from the attachment
            file_url = answer.attachments[0].url
            answers.append((questions[current_index]["tag"], file_url))
        elif validation_func is None or validation_func(answer.content):  # For non-image questions, validate the text
            answers.append((questions[current_index]["tag"], answer.content))  # Store the tag and answer pair
        else:
            error_message = INPUT_ERRORS.get(validation_func, "Invalid input. Please follow the format requirements.")
            await ctx.send(error_message)
            continue  # Ask again if input is invalid

        current_index += 1  # Move to next question

    # All questions answered, submit the theme
    submission_message = format_submission(ctx.author.id, *answers)
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(submission_message)

    await ctx.send("Your theme has been submitted successfully!")

@curator.command()
async def delete(ctx, message_id: int = None):
    """Allows a user to delete their own theme submission."""
    if message_id is None:
        await ctx.send("Please provide the message ID of the theme submission you wish to delete.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await ctx.send("Channel not found.")
        return

    try:
        message = await channel.fetch_message(message_id)

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
