import os
import logging
from flask import Flask
from threading import Thread

import nextcord
from nextcord.ext import commands

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)

# Flask app for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 1 is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot setup
intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents, help_command=None)

@bot.event
async def on_ready():
    """Bot is ready and logged in."""
    logger.info(f'Bot 1 logged in as {bot.user}')

# Run the bot
if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        logger.error("TOKEN environment variable not set!")
        print("ERROR: Please set the TOKEN environment variable!")
        exit(1)
    
    # Start Flask server for UptimeRobot
    keep_alive()
    
    # Run the bot
    bot.run(TOKEN)

