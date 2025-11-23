from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_menu_keyboard, cancel_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    
    if args == 'upload':
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "📸 Отправьте фотографию загрязнения.\n\n"
            "Вы можете:\n"
            "• Отправить фото напрямую\n"
            "• Отправить как файл (для сохранения метаданных GPS)\n\n"
            "Постарайтесь сфотографировать проблему чётко и с разных ракурсов.",
            reply_markup=cancel_keyboard()
        )
        return
    
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
