from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.keyboards import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🌍 Добро пожаловать в систему экологического мониторинга!\n\n"
        "Здесь вы можете:\n"
        "📸 Отправлять фото загрязнений\n"
        "📊 Смотреть свою статистику\n"
        "🗺 Просматривать карту всех загрязнений\n\n"
        "Давайте вместе сделаем наш город чище! 🌱",
        reply_markup=main_menu_keyboard()
    )
