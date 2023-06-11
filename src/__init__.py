import asyncio

from src.config import Config
from src.midjourney_bot import MidjourneyBot


def run():
    bot = MidjourneyBot(Config())
    asyncio.run(bot.start())
