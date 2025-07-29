# OI Alert Bot Documentation

OI Alert Bot is a Discord bot that fetches real-time Open Interest (OI) data for Bitcoin (BTC), Ethereum (ETH), and Altcoins from coinalyze.net, providing market insights and automated alerts to your Discord server.

## What is Open Interest?

**Open Interest (OI)** is the total number of outstanding derivative contracts, such as options or futures, that have not been settled. In the context of cryptocurrency markets, OI reflects the total value of active positions in the market. A rising OI can indicate increasing market activity and liquidity, while a declining OI may suggest positions are being closed and interest is waning. Monitoring OI helps traders gauge market sentiment and potential volatility.

## Features

- **Real-time OI Fetching:** Retrieves the latest OI data for BTC, ETH, and Altcoins using Selenium and undetected-chromedriver.
- **Discord Integration:** Responds to slash commands (`/btc`, `/eth`, `/alt`) with the current OI values.
- **Automated Alerts:** Monitors OI every 12 hours and sends an alert if the combined ETH + Altcoins OI surpasses BTC OI.

---

## How It Works

1. **Initialization:**

   - Loads environment variables (`DISCORD_TOKEN`, `CHANNEL_ID`) from the `.env` file.
   - Sets up a Discord bot with message content intent.
   - Initializes a headless Chrome browser using undetected-chromedriver and chromedriver-autoinstaller.

2. **Data Fetching:**

   - Navigates to coinalyze.net to scrape OI data for BTC, ETH, and Altcoins.
   - Uses CSS selectors to extract OI values from the site.
   - Parses and converts OI values to numeric format, handling billions and millions.

3. **Bot Commands:**

   - `/btc`: Replies with the current Bitcoin OI.
   - `/eth`: Replies with the current Ethereum OI.
   - `/alt`: Replies with the current Altcoin OI.

4. **Automated Monitoring:**

   - Every 12 hours, fetches OI data.
   - If `ETH OI + Altcoins OI > BTC OI`, sends an alert embed to the configured Discord channel.

---

## Setup & Installation

### Prerequisites

- **Python 3.12 or earlier**  
  (The `audioop` module required by `discord.py` is not available in Python 3.13+.)

### Installation Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/frhanjav/OI.git
   cd OI
   ```

2. **Create a Virtual Environment:**

   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables:**

   - Copy `.env.example` to `.env` and fill in your Discord bot token and channel ID:
     ```env
     DISCORD_TOKEN="your_discord_token_here"
     CHANNEL_ID="your_channel_id_here"
     ```

5. **Run the Bot:**
   ```bash
   python oi_alert_bot.py
   ```

---

## Usage

- **Add the bot to your Discord server.**
- Use the following slash commands:
  - `/btc` — Get current Bitcoin Open Interest.
  - `/eth` — Get current Ethereum Open Interest.
  - `/alt` — Get current Altcoin Open Interest.
- The bot will automatically send an alert if `ETH OI + Altcoins OI > BTC OI`.

---

## Environment Variables

- `DISCORD_TOKEN`: Your Discord bot token.
- `CHANNEL_ID`: The Discord channel ID where alerts will be sent.

---

## Dependencies

- `discord.py`: Discord API wrapper.
- `undetected-chromedriver`: For headless Chrome automation.
- `chromedriver-autoinstaller`: Automatically installs the correct ChromeDriver.
- `selenium`: Web automation.
- `beautifulsoup4`: HTML parsing.
- `python-dotenv`: Loads environment variables from `.env`.

---
