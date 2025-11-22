import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
# NEW: Import the keep_alive function
from keep_alive import keep_alive

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

# Define global lists for the challenge
TYPE_LIST = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
SCENARIO_LIST = ['Ura Finale', 'Unity Cup']
# Global variables for loaded lists/maps
UMALIST = []
UMA_IMAGE_MAP = {}
DEFAULT_IMAGE_URL = 'https://placehold.co/128x128/cccccc/555555?text=UMA'

# --- 2. FILE LOADING FUNCTIONS ---

# --- UPDATED FUNCTION: Load Image Map (single URL per line) ---
# Harmonized default filename to UmaPic.txt
def load_image_map(filename='UmaPic.txt'):
    """
    Loads the Uma Musume name-to-URL mapping from a file.
    It expects a single URL per line (Name | URL).
    """
    global UMA_IMAGE_MAP
    UMA_IMAGE_MAP = {}
    try:
        # Use the standard image map file
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Split the line by the pipe '|' separator (max split 1 for safety)
                parts = [p.strip() for p in line.split('|', 1)]
                
                if len(parts) == 2:
                    name, url = parts
                    # Store the single URL string as the dictionary value
                    UMA_IMAGE_MAP[name] = url
                    
        logging.info(f"Loaded {len(UMA_IMAGE_MAP)} Uma Musume images from {filename}.")
    except FileNotFoundError:
        # Added a direct print for better visibility if the file is missing
        print(f"CRITICAL ERROR: Image Map file '{filename}' not found. Images will not load.")
        logging.error(f"Image Map file '{filename}' not found. Using default placeholder image.")
    except Exception as e:
        logging.error(f"Error loading image map: {e}", exc_info=True)


def load_uma_list(filename='UmaList.txt'):
    """Loads the list of Uma Musume names from a text file."""
    global UMALIST
    try:
        # Load with UTF-8 encoding to handle international characters
        with open(filename, 'r', encoding='utf-8') as f:
            UMALIST = [line.strip() for line in f if line.strip()]
        if not UMALIST:
            logging.warning(f"File '{filename}' loaded, but it is empty.")
    except FileNotFoundError:
        logging.error(f"Critical Error: Character list file '{filename}' not found. Using fallback.")
        # Fallback list for stability during initialization
        UMALIST = ['Special Week', 'Tokai Teio', 'Oguri Cap']
        logging.info("Using temporary fallback list for UMALIST.")
    
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
    
    # Get the single image URL directly from the map
    image_url = UMA_IMAGE_MAP.get(random_uma, DEFAULT_IMAGE_URL)
    
    # Format the list of 6 types for clean display
    deck_str = ", ".join(random_deck_types)

    deck_suggestion = (
        f"Use a deck consisting of the following 6 types (5 Support Cards + 1 Borrow Card):"
        f"\n\n**{deck_str}**"
    )

    embed = discord.Embed(
        title=":trophy: Uma Musume Training Challenge :trophy:",
        description="Your goal: Clear the target scenario with the given Uma Musume and strategy.",
        color=0xf04d55 # Uma Musume themed red/pink
    )
    
    # embed.set_thumbnail(url=image_url) # Removed previously
    
    embed.add_field(name="Uma Musume", value=f"**{random_uma}**", inline=False)
    embed.add_field(name="Target Scenario", value=f"**{random_scenario}**", inline=False) 
    embed.add_field(name="Required Deck Composition", value=deck_suggestion, inline=False)
    
    # Set the image property, which displays a large image at the bottom of the embed
    embed.set_image(url=image_url) 
    
    return embed

# --- 4. VIEW (BUTTON) CLASS ---

class ChallengeView(discord.ui.View):
    """A persistent view that provides a button to regenerate the challenge."""
    def __init__(self):
        super().__init__(timeout=300) 

    @discord.ui.button(label="Regenerate Challenge", style=discord.ButtonStyle.red, emoji="🔄")
    async def regenerate_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer() 
        
        try:
            new_embed = generate_challenge_embed()
            await interaction.message.edit(embed=new_embed, view=self)
            await interaction.followup.send("New challenge generated!", ephemeral=True)

        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
        except Exception as e:
            logging.error("Error during challenge regeneration button click.", exc_info=True)
            await interaction.followup.send("An unexpected error occurred. Check the log.", ephemeral=True)

# --- 5. BOT EVENTS ---
@bot.event
async def on_ready():
    # Load all external files on startup
    load_uma_list()
    # Now correctly loads the default 'UmaPic.txt'
    load_image_map() 
    loaded_count = len(UMALIST)
    image_map_count = len(UMA_IMAGE_MAP)
    
    print('--- Bot Ready Status ---')
    print(f'Logged in as {bot.user.name}')
    print(f'Loaded {loaded_count} Uma Musume characters from UmaList.txt.')
    print(f'Loaded {image_map_count} image mappings from UmaPic.txt.')
    print(f'Bot Prefix: {bot.command_prefix}')
    print('------------------------')

# This event handler catches errors outside the command structure
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
            await ctx.send(f"**Permission Error:** I failed to respond to your command due to missing permissions. Please fix my server permissions.")
        except:
            pass
        return

    logging.error(f"--- COMMAND EXECUTION ERROR in {ctx.command} ---", exc_info=True)
    await ctx.send(f"**Command Failed:** An unexpected internal error occurred. Please check the `discord.log` file for the traceback.")


# --- 6. BOT COMMANDS ---
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

@bot.command()
async def challenge(ctx):
    """Generates a random Uma Musume training challenge."""
    if not UMALIST:
        await ctx.send('**Critical Error:** The Uma Musume list is empty! Cannot generate a challenge. Please run `!list` to check the status.')
        return

    try:
        embed = generate_challenge_embed()
        view = ChallengeView()
        await ctx.send(embed=embed, view=view)
        
    except ValueError as e:
        await ctx.send(f"Error: {e}")
    except Exception as e:
        logging.error("Exception during initial !challenge send.", exc_info=True)
        await ctx.send(f"**Command Failed:** An unexpected error occurred. Please check the `discord.log` file.")
        
# --- 7. EXECUTION ---
if token:
    print("Attempting to run bot...")
    # DIAGNOSTIC STEP: Comment out keep_alive to see if it stops the double post.
    # keep_alive() 
    bot.run(token, log_handler=handler)
else:
    print("Error: Discord token not found. Please ensure 'Discord_token' is set in your .env file.")
