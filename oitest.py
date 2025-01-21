import discord
from discord.ext import commands, tasks
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Validate the token and channel ID
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing in the .env file")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is missing in the .env file")

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fetch OI data
def fetch_oi_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        # Fetch BTC OI from Velo
        velo_response = requests.get("https://coinalyze.net/?categories=1")
        velo_response.raise_for_status()
        btc_oi = parse_btc_oi(velo_response.text)  # Implement parse_oi_from_velo()

        # Fetch altcoins OI from Coinalyze
        coinalyze_response = requests.get("https://coinalyze.net/?categories=1")
        coinalyze_response.raise_for_status()
        alt_oi = parse_alt_oi(coinalyze_response.text)  # Implement parse_oi_from_coinalyze()

        return btc_oi, alt_oi
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None

# Parsing functions
def parse_btc_oi(html):
    """Parse Bitcoin OI from Velo"""
    soup = BeautifulSoup(html, "html.parser")
    # Example: Update the selector based on Velo's HTML structure
    btc_oi_element = soup.select_one("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(6)")  # Replace with correct selector
    if btc_oi_element:
        return float(btc_oi_element.text.replace(",", ""))
    return 0

def parse_alt_oi(html):
    """Parse Altcoin OI from Coinalyze"""
    soup = BeautifulSoup(html, "html.parser")
    # Use the confirmed selector to get Alt OI
    alt_oi_element = soup.select_one(
        "body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(2) > td:nth-child(6)"
    )
    if alt_oi_element:
        return float(alt_oi_element.text.replace(",", ""))
    return 0

# Background task to monitor OI
@tasks.loop(minutes=1)
async def monitor_oi():
    btc_oi, alt_oi = fetch_oi_data()
    if btc_oi is None or alt_oi is None:
        print("Error fetching OI data.")
        return  # Skip if there was an error fetching data

    # Print the fetched OI values for reference
    print(f"BTC OI: {btc_oi}, Alt OI: {alt_oi}")

    # Check if Alt OI exceeds BTC OI
    if alt_oi > btc_oi:
        channel = bot.get_channel(int(CHANNEL_ID))
        if channel:
            await channel.send(
                f"🚨 Alert: Altcoins OI ({alt_oi}) has surpassed Bitcoin OI ({btc_oi})!"
            )
        print(f"Alert sent: Alt OI ({alt_oi}) > BTC OI ({btc_oi})")
    else:
        print(f"No alert: Alt OI ({alt_oi}) <= BTC OI ({btc_oi})")

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")
    monitor_oi.start()

# Run the bot
bot.run(DISCORD_TOKEN)
