import discord
from discord.ext import commands, tasks
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Validate environment variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing in the .env file")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is missing in the .env file")

# Initialize bot with required intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

def fetch_oi_data():
    session = requests.Session()
    headers = get_headers()
    
    try:
        # First fetch BTC OI from main page
        print("Fetching BTC OI...")
        btc_response = session.get("https://coinalyze.net/", headers=headers)
        btc_response.raise_for_status()
        btc_oi = parse_btc_oi(btc_response.text)
        
        # Wait a bit between requests
        time.sleep(2)
        
        # Then fetch ALTS OI
        print("Fetching ALTS OI...")
        alts_response = session.get("https://coinalyze.net/?categories=1", headers=headers)
        alts_response.raise_for_status()
        alt_oi = parse_alt_oi(alts_response.text)
        
        print(f"Raw BTC OI: {btc_oi}")
        print(f"Raw ALT OI: {alt_oi}")
        
        return btc_oi, alt_oi
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None, None

def parse_btc_oi(html):
    """Parse Bitcoin OI from the main page"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        btc_oi_element = soup.select_one("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(7)")
        
        if btc_oi_element:
            # Remove any currency symbols and commas, convert to float
            oi_text = btc_oi_element.text.strip()
            oi_text = oi_text.replace("$", "").replace(",", "")
            return float(oi_text)
        else:
            print("BTC OI element not found")
            return 0
    except Exception as e:
        print(f"Error parsing BTC OI: {e}")
        return 0

def parse_alt_oi(html):
    """Parse Altcoin OI from the categories page"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        alt_oi_element = soup.select_one("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(2) > td:nth-child(6)")
        
        if alt_oi_element:
            # Remove any currency symbols and commas, convert to float
            oi_text = alt_oi_element.text.strip()
            oi_text = oi_text.replace("$", "").replace(",", "")
            return float(oi_text)
        else:
            print("ALT OI element not found")
            return 0
    except Exception as e:
        print(f"Error parsing ALT OI: {e}")
        return 0

@tasks.loop(minutes=5)
async def monitor_oi():
    btc_oi, alt_oi = fetch_oi_data()
    
    if btc_oi is None or alt_oi is None:
        print("Error fetching OI data.")
        return

    print(f"BTC OI: ${btc_oi:,.2f}, Alt OI: ${alt_oi:,.2f}")

    if alt_oi > btc_oi:
        channel = bot.get_channel(int(CHANNEL_ID))
        if channel:
            embed = discord.Embed(
                title="🚨 Open Interest Alert",
                description="Altcoins Open Interest has surpassed Bitcoin Open Interest!",
                color=discord.Color.red()
            )
            embed.add_field(name="Bitcoin OI", value=f"${btc_oi:,.2f}", inline=True)
            embed.add_field(name="Altcoins OI", value=f"${alt_oi:,.2f}", inline=True)
            embed.add_field(name="Difference", value=f"${(alt_oi - btc_oi):,.2f}", inline=False)
            
            await channel.send(embed=embed)
        else:
            print(f"Error: Could not find channel with ID {CHANNEL_ID}")
    else:
        print(f"No alert needed. Alt OI (${alt_oi:,.2f}) is lower than BTC OI (${btc_oi:,.2f})")

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")
    monitor_oi.start()

# Run the bot
bot.run(DISCORD_TOKEN)