from aiogram import Router, F
from aiogram.types import Message
from bot.utils import get_user_stats

router = Router()

@router.message(F.text == "📊 Моя статистика")
async def show_stats(message: Message):
    stats = await get_user_stats(message.from_user.id)
    
    if not stats:
        await message.answer("❌ Данные не найдены")
        return
    
    status_emoji = {
        'new': '🆕',
        'reviewing': '👀',
        'in_progress': '🔧',
        'resolved': '✅',
        'rejected': '❌'
    }
    
    status_names = {
        'new': 'Новые',
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решённые',
        'rejected': 'Отклонённые'
    }
    
    reports_text = "\n".join([
        f"{status_emoji[status]} {status_names[status]}: {count}"
        for status, count in stats['reports_by_status'].items()
        if count > 0
    ])
    
    if not reports_text:
        reports_text = "Нет отчётов"

    username = stats.get("username")
    user = f"@{username}" if username else message.from_user.first_name

    text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"👤 Пользователь: {user}\n"
        f"📝 Всего отчётов: {stats['reports_count']}\n"
        f"⭐️ Рейтинг: {stats['rating']}\n"
        f"🏆 Место в рейтинге: #{stats['rank']}\n\n"
        f"<b>Ваши отчёты:</b>\n{reports_text}"
    )
    
    await message.answer(text, parse_mode='HTML')
