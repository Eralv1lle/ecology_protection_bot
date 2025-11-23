import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from bot.handlers import start, stats, photo, admin, review
from bot.middlewares import UserMiddleware
from database import initialize_db

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    initialize_db()
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.message.middleware(UserMiddleware())
    
    dp.include_router(start.router)
    dp.include_router(stats.router)
    dp.include_router(photo.router)
    dp.include_router(admin.router)
    dp.include_router(review.router)

    logger.info("Bot started")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
