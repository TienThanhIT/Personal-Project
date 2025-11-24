import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import time
from host import keep_alive

# --- 1. CONFIGURATION AND INITIALIZATION ---
load_dotenv()
token = os.getenv('Discord_token')

# Set up logging to file
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

# --- GLOBAL BOT STATE FLAG ---
# CRITICAL FIX for double execution: This flag ensures on_ready only runs once.
bot.is_ready_flag = False

# Define global lists for the challenge
TYPE_LIST = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
SCENARIO_LIST = ['Ura Finale', 'Unity Cup']
# Global variables for loaded lists/maps
UMALIST = []
UMA_IMAGE_MAP = {}
DEFAULT_IMAGE_URL = 'https://placehold.co/128x128/cccccc/555555?text=UMA'

# --- 2. FILE LOADING FUNCTIONS ---
def load_image_map(filename='UmaPic.txt'):
    """
    Loads the Uma Musume name-to-URL mapping from a file.
    """
    global UMA_IMAGE_MAP
    UMA_IMAGE_MAP = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Assuming the actual file name is 'UmaPic.txt' based on the user's file content
                parts = [p.strip() for p in line.split('|', 1)] 
                
                if len(parts) == 2:
                    name, url = parts
                    UMA_IMAGE_MAP[name] = url
                    
        logging.info(f"Loaded {len(UMA_IMAGE_MAP)} Uma Musume images from {filename}.")
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Image Map file '{filename}' not found. Images will not load.")
        logging.error(f"Image Map file '{filename}' not found. Using default placeholder image.")
    except Exception as e:
        logging.error(f"Error loading image map: {e}", exc_info=True)


def load_uma_list(filename='UmaList.txt'):
    """Loads the list of Uma Musume names from a text file."""
    global UMALIST
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            UMALIST = [line.strip() for line in f if line.strip()]

        print(f"--- DIAGNOSTIC: Loaded {len(UMALIST)} characters from '{filename}'. ---")
        if not UMALIST:
            logging.warning(f"File '{filename}' loaded, but it is empty.")
    except FileNotFoundError:
        logging.error(f"Critical Error: Character list file '{filename}' not found. Using fallback.")
        UMALIST = ['Special Week', 'Tokai Teio', 'Oguri Cap']
        logging.info("Using temporary fallback list for UMALIST.")
        print(f"--- DIAGNOSTIC: Used Fallback List of size {len(UMALIST)}. ---")
    
    return UMALIST

# --- 3. CORE LOGIC FUNCTION ---
def generate_challenge_embed():
    """Generates the challenge embed, ensuring UMALIST is ready."""
    global UMALIST, UMA_IMAGE_MAP
    if not UMALIST:
        raise ValueError("Uma Musume list is empty. Cannot generate challenge.")

    random_uma = random.choice(UMALIST)
    random_deck_types = random.choices(TYPE_LIST, k=6) 
    random_scenario = random.choice(SCENARIO_LIST)
    
    image_url = UMA_IMAGE_MAP.get(random_uma, DEFAULT_IMAGE_URL)
    
    deck_str = ", ".join(random_deck_types)

    deck_suggestion = (
        f"Use a deck consisting of the following 6 types (5 Support Cards + 1 Borrow Card):"
        f"\n\n**{deck_str}**"
    )

    embed = discord.Embed(
        title=":trophy: Uma Musume Training Challenge :trophy:",
        description="Your goal: Clear the target scenario with the given Uma Musume and card types.",
        color=0xf04d55 # Uma Musume themed red/pink
    )
    
    embed.add_field(name="Uma Musume", value=f"**{random_uma}**", inline=False)
    embed.add_field(name="Target Scenario", value=f"**{random_scenario}**", inline=False) 
    embed.add_field(name="Required Deck Composition", value=deck_suggestion, inline=False)
    
    # Note: We use set_image instead of set_thumbnail for a large focus on the Uma's picture.
    embed.set_image(url=image_url) 
    
    return embed

# --- 4. VIEW (BUTTON) CLASS ---
class ChallengeView(discord.ui.View):
    """A persistent view that provides a button to regenerate the challenge."""
    # MODIFICATION: Accept and store the user ID of the original command author
    def __init__(self, original_user_id):
        super().__init__(timeout=300) 
        self.original_user_id = original_user_id

    # Add a check to ensure only the original user can interact
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.original_user_id:
            await interaction.response.send_message(
                "Sorry, only the user who initiated the challenge can regenerate it.", 
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Regenerate Challenge", style=discord.ButtonStyle.red, emoji="🔄")
    async def regenerate_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Acknowledge the interaction immediately to avoid timeout
        await interaction.response.defer() 
        
        try:
            new_embed = generate_challenge_embed()
            # Edit the original message to show the new challenge
            await interaction.message.edit(embed=new_embed, view=self)

        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
        except Exception as e:
            logging.error("Error during challenge regeneration button click.", exc_info=True)
            await interaction.followup.send("An unexpected error occurred. Check the log.", ephemeral=True)

# --- 5. BOT EVENTS ---
@bot.event
async def on_ready():
    # --- CRITICAL DOUBLE-RUN CHECK (First Defense Layer) ---
    # This prevents duplicate command loading if the Discord client reconnects.
    if bot.is_ready_flag:
        print('--- WARNING: Redundant on_ready event detected. Ignoring. ---')
        return

    # Set the flag to True on the first successful run.
    bot.is_ready_flag = True
    # ---------------------------------
    
    # Load all external files on startup
    load_uma_list()
    load_image_map() 
    loaded_count = len(UMALIST)
    image_map_count = len(UMA_IMAGE_MAP)
    
    print('--- Bot Ready Status ---')
    print(f'Logged in as {bot.user.name}')
    print(f'Loaded {loaded_count} Uma Musume characters from UmaList.txt.')
    print(f'Loaded {image_map_count} image mappings from UmaPic.txt.')
    print(f'Bot Prefix: {bot.command_prefix}')
    print('------------------------')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, discord.errors.Forbidden):
        error_message = f"Error code 50013: Missing Permissions. Please ensure the bot has **Send Messages** and **Embed Links** permissions in this channel."
        print(f"--- COMMAND EXECUTION ERROR ---")
        print(f"FORBIDDEN ERROR: {error_message}")
        print("-------------------------------")
        try:
            # Only try to send an error message if possible
            await ctx.send(f"**Permission Error:** I failed to respond to your command due to missing permissions. Please fix my server permissions.")
        except:
            pass
        return

    logging.error(f"--- COMMAND EXECUTION ERROR in {ctx.command} ---", exc_info=True)
    await ctx.send(f"**Command Failed:** An unexpected internal error occurred. Please check the `discord.log` file for the traceback.")


# --- 6. BOT COMMANDS ---
# Cache for message IDs already responded to. This is the last line of defense
# against duplicate processes reading the same command message.
processed_messages = set()

@bot.command()
async def ping(ctx):
    """Checks bot responsiveness."""
    await ctx.send('Bot ready! Latency: {0}ms'.format(round(bot.latency * 1000)))

@bot.command(name='list') 
async def list_uma(ctx):
    """Shows how many Uma Musume characters were loaded."""
    if UMALIST:
        await ctx.send(f"Successfully loaded **{len(UMALIST)}** Uma Musume characters!")
    else:
        await ctx.send("The Uma Musume list is currently **empty**. Please ensure `UmaList.txt` exists and has entries.")

# Cache for message IDs already responded to. This is the last line of defense
# against duplicate processes reading the same command message.
processed_messages = set()

@bot.command()
async def urc(ctx):
    # ...
    # --- AGGRESSIVE DUPLICATE COMMAND CHECK (Final Defense Layer) ---
    # 1. Check if we've processed this message ID before.
    if ctx.message.id in processed_messages:
        print(f"--- DUPLICATE MESSAGE ID {ctx.message.id} detected. Skipping response. ---")
        return
    
    # 2. If it's new, mark it as processed immediately.
    processed_messages.add(ctx.message.id)
    print(f"--- MESSAGE ID {ctx.message.id} added to processed_messages set. ---")
    # -----------------------------------------------------------
    # ...


    if not UMALIST:
        await ctx.send('**Critical Error:** The Uma Musume list is empty! Cannot generate a challenge. Please run `!list` to check the status.')
        return

    try:
        embed = generate_challenge_embed()
        # MODIFICATION: Pass the author's ID to the ChallengeView
        view = ChallengeView(original_user_id=ctx.author.id)
        await ctx.send(embed=embed, view=view)
        
    except ValueError as e:
        await ctx.send(f"Error: {e}")
    except Exception as e:
        logging.error("Exception during initial !challenge send.", exc_info=True)
        await ctx.send(f"**Command Failed:** An unexpected error occurred. Please check the `discord.log` file.")
        
# --- 7. EXECUTION ---
if token:
    print("Attempting to run bot...")
    # Start the Flask web server thread
    keep_alive() 
    # Give the web server a moment to start before running the bot
    time.sleep(1) 
    # Start the Discord bot
    bot.run(token, log_handler=handler)
else:
    print("Error: Discord token not found. Please ensure 'Discord_token' is set in your .env file.")



