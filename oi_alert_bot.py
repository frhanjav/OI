import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import chromedriver_autoinstaller

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

# Initialize Chrome driver
driver = None

def format_number(value):
    """Convert number to billions/millions format with B/M suffix"""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    else:
        return f"${value:,.2f}"

def initialize_driver():
    global driver
    try:
        chromedriver_autoinstaller.install()
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        chrome_version = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
        
        driver = uc.Chrome(
            options=options,
            version_main=int(chrome_version)
        )
        driver.set_page_load_timeout(30)
        return True
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return False

def wait_for_element(selector, timeout=20):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        driver.save_screenshot("debug_screenshot.png")
        return None
    except Exception as e:
        print(f"Error waiting for element {selector}: {e}")
        return None

async def retry_fetch_oi_data(max_retries=3):
    for attempt in range(max_retries):
        btc_oi, eth_oi, alt_oi = fetch_oi_data()
        if all(x is not None for x in [btc_oi, eth_oi, alt_oi]):
            return btc_oi, eth_oi, alt_oi
        print(f"Attempt {attempt + 1} failed, reinitializing driver...")
        await cleanup_driver()
        time.sleep(5)
    return None, None, None

async def cleanup_driver():
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None

def parse_oi_value(element):
    try:
        if element:
            oi_text = element.text.strip()
            print(f"Raw text found: {oi_text}")
            
            oi_text = oi_text.replace("$", "").replace(",", "")
            
            if 'b' in oi_text.lower():
                oi_text = oi_text.lower().replace('b', '')
                return float(oi_text) * 1_000_000_000
            elif 'm' in oi_text.lower():
                oi_text = oi_text.lower().replace('m', '')
                return float(oi_text) * 1_000_000
            return float(oi_text)
        return 0
    except Exception as e:
        print(f"Error parsing OI value: {e}")
        return 0

def fetch_oi_data():
    global driver
    
    try:
        if driver is None:
            if not initialize_driver():
                return None, None, None

        # Fetch BTC and ETH OI
        print("Fetching BTC and ETH OI...")
        driver.get("https://coinalyze.net/")
        time.sleep(10)
        
        btc_element = wait_for_element("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(7)")
        eth_element = wait_for_element("body > div.body-wrapper > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(2) > td:nth-child(7)")
        
        btc_oi = parse_oi_value(btc_element) if btc_element else 0
        eth_oi = parse_oi_value(eth_element) if eth_element else 0
        
        # Fetch ALTS OI
        print("Fetching ALTS OI...")
        driver.get("https://coinalyze.net/?categories=1")
        time.sleep(10)
        
        alt_element = wait_for_element("body > div.body-wrapper > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(3) > td:nth-child(6)")
        alt_oi = parse_oi_value(alt_element) if alt_element else 0
        
        return btc_oi, eth_oi, alt_oi
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        try:
            if driver:
                driver.save_screenshot("error_screenshot.png")
        except:
            pass
        return None, None, None

@tasks.loop(hours=12)
async def monitor_oi():
    btc_oi, eth_oi, alt_oi = await retry_fetch_oi_data()
    
    if any(x is None for x in [btc_oi, eth_oi, alt_oi]):
        print("Error fetching OI data after all retries.")
        return

    combined_alt_eth_oi = alt_oi + eth_oi
    
    if combined_alt_eth_oi > btc_oi:
        channel = bot.get_channel(int(CHANNEL_ID))
        if channel:
            embed = discord.Embed(
                title="🚨 Combined Open Interest Alert",
                description="Combined ETH + Altcoins Open Interest has surpassed Bitcoin Open Interest!",
                color=discord.Color.red()
            )
            embed.add_field(name="Bitcoin OI", value=format_number(btc_oi), inline=True)
            embed.add_field(name="ETH OI", value=format_number(eth_oi), inline=True)
            embed.add_field(name="Altcoins OI", value=format_number(alt_oi), inline=True)
            embed.add_field(name="Combined ETH + Alts", value=format_number(combined_alt_eth_oi), inline=True)
            embed.add_field(name="Difference", value=format_number(combined_alt_eth_oi - btc_oi), inline=False)
            
            await channel.send(embed=embed)
        else:
            print(f"Error: Could not find channel with ID {CHANNEL_ID}")

@bot.tree.command(name="btc", description="Get Bitcoin Open Interest")
async def btc(interaction: discord.Interaction):
    await interaction.response.defer()
    btc_oi, _, _ = await retry_fetch_oi_data()
    if btc_oi is not None:
        embed = discord.Embed(
            title="Bitcoin Open Interest",
            description=f"Current BTC OI: {format_number(btc_oi)}",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Error fetching Bitcoin OI data")

@bot.tree.command(name="eth", description="Get Ethereum Open Interest")
async def eth(interaction: discord.Interaction):
    await interaction.response.defer()
    _, eth_oi, _ = await retry_fetch_oi_data()
    if eth_oi is not None:
        embed = discord.Embed(
            title="Ethereum Open Interest",
            description=f"Current ETH OI: {format_number(eth_oi)}",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Error fetching Ethereum OI data")

@bot.tree.command(name="alt", description="Get Altcoin Open Interest")
async def alt(interaction: discord.Interaction):
    await interaction.response.defer()
    _, _, alt_oi = await retry_fetch_oi_data()
    if alt_oi is not None:
        embed = discord.Embed(
            title="Altcoin Open Interest",
            description=f"Current ALT OI: {format_number(alt_oi)}",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("Error fetching Altcoin OI data")

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
    if initialize_driver():
        monitor_oi.start()
    else:
        print("Failed to initialize Chrome driver. Bot cannot start monitoring.")

@bot.event
async def on_disconnect():
    await cleanup_driver()

# Run the bot
try:
    bot.run(DISCORD_TOKEN)
finally:
    if driver:
        driver.quit()