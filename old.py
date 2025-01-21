import discord
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

def initialize_driver():
    global driver
    try:
        options = uc.ChromeOptions()
        # Remove headless mode to debug
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        driver = uc.Chrome(options=options)
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
        # Take screenshot for debugging
        driver.save_screenshot("debug_screenshot.png")
        print(f"Debug screenshot saved as debug_screenshot.png")
        # Print page source for debugging
        print("Page source:")
        print(driver.page_source[:500] + "...")  # Print first 500 chars
        return None
    except Exception as e:
        print(f"Error waiting for element {selector}: {e}")
        return None

def fetch_oi_data():
    global driver
    
    try:
        if driver is None:
            if not initialize_driver():
                return None, None

        # Fetch BTC OI
        print("Fetching BTC OI...")
        driver.get("https://coinalyze.net/")
        time.sleep(10)  # Increased wait time
        
        print("Looking for BTC OI element...")
        btc_element = wait_for_element("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(7)")
        btc_oi = parse_oi_value(btc_element) if btc_element else 0
        
        # Fetch ALTS OI
        print("Fetching ALTS OI...")
        driver.get("https://coinalyze.net/?categories=1")
        time.sleep(10)  # Increased wait time
        
        print("Looking for ALT OI element...")
        alt_element = wait_for_element("body > div > div.main-content > div > div.listing > div.table-wrapper > table > tbody > tr:nth-child(2) > td:nth-child(6)")
        alt_oi = parse_oi_value(alt_element) if alt_element else 0
        
        print(f"Raw BTC OI: {btc_oi}")
        print(f"Raw ALT OI: {alt_oi}")
        
        return btc_oi, alt_oi
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        try:
            if driver:
                driver.save_screenshot("error_screenshot.png")
                print("Error screenshot saved as error_screenshot.png")
        except:
            pass
        return None, None

def parse_oi_value(element):
    try:
        if element:
            oi_text = element.text.strip()
            print(f"Raw text found: {oi_text}")
            oi_text = oi_text.replace("$", "").replace(",", "")
            return float(oi_text)
        return 0
    except Exception as e:
        print(f"Error parsing OI value: {e}")
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
    if initialize_driver():
        monitor_oi.start()
    else:
        print("Failed to initialize Chrome driver. Bot cannot start monitoring.")

@bot.event
async def on_disconnect():
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None

# Run the bot
try:
    bot.run(DISCORD_TOKEN)
finally:
    if driver:
        driver.quit()