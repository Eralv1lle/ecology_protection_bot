from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import os
from dotenv import load_dotenv

from bot.keyboards import admin_menu_keyboard, main_menu_keyboard, report_status_keyboard, pagination_keyboard, cancel_admin_keyboard
from bot.utils import get_reports, update_report_status, delete_report
from database import Admin, db
from bot.utils import create_admin

load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

router = Router()

ITEMS_PER_PAGE = 5

class AdminStates(StatesGroup):
    waiting_for_password = State()

def is_admin(telegram_id):
    db.connect(reuse_if_open=True)
    try:
        admin = Admin.get((Admin.telegram_id == telegram_id) & (Admin.is_active == True))
        db.close()
        return True
    except:
        db.close()
        return False

@router.message(Command("admin"))
async def admin_login(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer(
            "👨‍💼 Вы вошли в админ-панель",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await state.set_state(AdminStates.waiting_for_password)
        await message.answer("Введите пароль администратора:", reply_markup=cancel_admin_keyboard())

@router.message(F.text == "Отмена ❌")
async def cancel_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Вход в админ-панель отменён",
        reply_markup=main_menu_keyboard()
    )

@router.message(AdminStates.waiting_for_password)
async def check_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        create_admin(message.from_user.id)
        await message.answer(
            "👨‍💼 Вы вошли в админ-панель",
            reply_markup=admin_menu_keyboard()
        )
        await state.clear()
    else:
        await message.answer("❌ Неверный пароль, попробуйте ещё раз", reply_markup=cancel_admin_keyboard())

@router.message(F.text == "🔙 Выйти из админки")
async def admin_logout(message: Message):
    await message.answer(
        "👋 Вы вышли из админ-панели",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.text == "📋 Новые отчёты")
async def show_new_reports(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    reports = await get_reports(status='new')

    if not reports:
        await message.answer("📋 Нет новых отчётов")
        return

    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')

    for i, report in enumerate(reports[:ITEMS_PER_PAGE]):
        text = (
            f"📋 <b>Отчёт #{report['id']}</b>\n\n"
            f"👤 Пользователь: @{report.get('username', 'Неизвестно')}\n"
            f"🗑 Тип отходов: {report['waste_type']}\n"
            f"⚠️ Опасность: {report['danger_level']}\n"
            f"📍 Координаты: {report['latitude']}, {report['longitude']}\n"
            f"📝 Описание: {report['description']}\n"
            f"📅 Дата: {report['created_at'][:10]}"
        )

        photo_url = f"{backend_url}/uploads/{report['photo_path']}"

        try:
            await message.answer_photo(
                photo=photo_url,
                caption=text,
                parse_mode='HTML',
                reply_markup=report_status_keyboard(report['id'])
            )
        except:
            await message.answer(
                text,
                parse_mode='HTML',
                reply_markup=report_status_keyboard(report['id'])
            )

@router.message(F.text == "🔍 Все отчёты")
async def show_all_reports(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    reports = await get_reports()

    if not reports:
        await message.answer("📋 Нет отчётов")
        return

    total_pages = (len(reports) - 1) // ITEMS_PER_PAGE + 1

    text = f"📋 <b>Все отчёты</b>\n\n"
    text += f"Всего отчётов: {len(reports)}\n\n"

    for report in reports[:ITEMS_PER_PAGE]:
        status_emoji = {
            'new': '🆕',
            'reviewing': '👀',
            'in_progress': '🔧',
            'resolved': '✅',
            'rejected': '❌'
        }

        text += (
            f"{status_emoji.get(report['status'], '❓')} "
            f"#{report['id']} - {report['waste_type']} "
            f"(@{report.get('username', 'Неизвестно')})\n"
        )

    await message.answer(
        text,
        parse_mode='HTML',
        reply_markup=pagination_keyboard(0, total_pages, 'all_reports') if total_pages > 1 else None
    )

@router.callback_query(F.data.startswith("status_"))
async def change_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    parts = callback.data.split("_", maxsplit=2)
    report_id = int(parts[1])
    new_status = parts[2]

    status_names = {
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решён',
        'rejected': 'Отклонён'
    }

    await update_report_status(
        report_id=report_id,
        status=new_status,
        changed_by=callback.from_user.id,
        comment=f"Изменено администратором @{callback.from_user.username}"
    )

    await callback.answer(
        f"✅ Статус изменён на: {status_names[new_status]}",
        show_alert=True
    )

    await callback.message.edit_reply_markup(reply_markup=None)

@router.callback_query(F.data.startswith("delete_"))
async def delete_report_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    report_id = int(callback.data.split("_")[1])

    await delete_report(report_id)

    await callback.answer("🗑 Отчёт удалён", show_alert=True)
    await callback.message.delete()

@router.message(F.text == "👥 Пользователи")
async def show_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    from database import User

    db.connect(reuse_if_open=True)
    users = list(User.select().order_by(User.rating.desc()).limit(20))
    db.close()

    text = "👥 <b>Топ пользователей:</b>\n\n"

    for i, user in enumerate(users, 1):
        text += (
            f"{i}. @{user.username or 'Неизвестно'} - "
            f"{user.reports_count} отчётов, "
            f"{user.rating} ⭐️\n"
        )

    await message.answer(text, parse_mode='HTML')
