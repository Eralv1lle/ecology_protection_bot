from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

import os
import math

from bot.keyboards import admin_menu_keyboard, main_menu_keyboard, cancel_keyboard, cancel_admin_keyboard
from bot.utils import get_reports, update_report_status, delete_report
from database import Admin, User, db, Review


router = Router()

ITEMS_PER_PAGE = 10

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

def create_pagination_keyboard(items, page, total_pages, prefix, callback_data_template):
    keyboard = []
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(items))
    
    for i in range(start_idx, end_idx):
        item = items[i]
        keyboard.append([InlineKeyboardButton(
            text=callback_data_template(item),
            callback_data=f"{prefix}_{item['id'] if isinstance(item, dict) else item.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("admin"))
async def admin_login(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer(
            "👨‍💼 Добро пожаловать в админ-панель!",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await state.set_state(AdminStates.waiting_for_password)
        await message.answer(
            "🔐 Введите пароль администратора:",
            reply_markup=cancel_admin_keyboard()
        )

@router.message(F.text == "Отмена ❌")
async def cancel_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Вход в админ-панель отменён",
        reply_markup=main_menu_keyboard()
    )

@router.message(AdminStates.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext):
    if message.text == os.getenv('ADMIN_PASSWORD'):
        db.connect(reuse_if_open=True)
        try:
            admin = Admin.get(Admin.telegram_id == message.from_user.id)
            admin.is_active = True
            admin.save()
        except:
            Admin.create(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                is_active=True
            )
        db.close()
        
        await state.clear()
        await message.answer(
            "✅ Вы успешно авторизованы как администратор!",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await message.answer("❌ Неверный пароль. Попробуйте снова:", reply_markup=cancel_admin_keyboard())

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
    
    total_pages = math.ceil(len(reports) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        reports, 
        0, 
        total_pages, 
        "new_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} ({r['danger_level']})"
    )
    
    await message.answer(
        f"📋 <b>Новые отчёты</b>\n\n"
        f"Всего: {len(reports)}\n"
        f"Выберите отчёт для просмотра:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.message(F.text == "💬 Отзывы")
async def show_reviews_list(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    db.connect(reuse_if_open=True)
    reviews = list(Review.select().order_by(Review.created_at.desc()))
    db.close()

    if not reviews:
        await message.answer("💬 Нет отзывов")
        return

    total_pages = math.ceil(len(reviews) / ITEMS_PER_PAGE)

    keyboard = create_pagination_keyboard(
        reviews,
        0,
        total_pages,
        "review",
        lambda r: f"⭐ @{r.user.username or 'Неизвестно'} - {r.text[:30]}..."
    )

    await message.answer(
        f"💬 <b>Отзывы</b>\n\n"
        f"Всего: {len(reviews)}\n"
        f"Выберите отзыв:",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("review_page_"))
async def reviews_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])

    db.connect(reuse_if_open=True)
    reviews = list(Review.select().order_by(Review.created_at.desc()))
    db.close()

    total_pages = math.ceil(len(reviews) / ITEMS_PER_PAGE)

    keyboard = create_pagination_keyboard(
        reviews,
        page,
        total_pages,
        "review",
        lambda r: f"⭐ @{r.user.username or 'Неизвестно'} - {r.text[:30]}..."
    )

    await callback.message.edit_text(
        f"💬 <b>Отзывы</b>\n\n"
        f"Всего: {len(reviews)}\n"
        f"Страница {page + 1}/{total_pages}\n"
        f"Выберите отзыв:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("review_") & ~F.data.contains("page"))
async def show_review_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    review_id = int(callback.data.split("_")[-1])

    db.connect(reuse_if_open=True)
    try:
        review = Review.get_by_id(review_id)
    except:
        await callback.answer("❌ Отзыв не найден", show_alert=True)
        db.close()
        return

    text = (
        f"⭐ <b>Отзыв #{review.id}</b>\n\n"
        f"👤 Пользователь: @{review.user.username or 'Неизвестно'}\n"
        f"📝 Текст:\n{review.text}\n\n"
        f"📅 Дата: {review.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    db.close()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить отзыв", callback_data=f"delete_review_{review_id}")],
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_reviews")]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_review_"))
async def delete_review_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    review_id = int(callback.data.split("_")[-1])

    import aiohttp
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')

    async with aiohttp.ClientSession() as session:
        async with session.delete(f'{backend_url}/api/reviews/{review_id}') as response:
            if response.status == 200:
                await callback.answer("🗑 Отзыв удалён", show_alert=True)

                try:
                    await callback.message.delete()
                except:
                    pass
            else:
                await callback.answer("❌ Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "back_to_reviews")
async def back_to_reviews_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    db.connect(reuse_if_open=True)
    reviews = list(Review.select().order_by(Review.created_at.desc()))
    db.close()

    if not reviews:
        await callback.message.answer("💬 Нет отзывов")
        await callback.answer()
        return

    total_pages = math.ceil(len(reviews) / ITEMS_PER_PAGE)

    keyboard = create_pagination_keyboard(
        reviews,
        0,
        total_pages,
        "review",
        lambda r: f"⭐ @{r.user.username or 'Неизвестно'} - {r.text[:30]}..."
    )

    await callback.message.answer(
        f"💬 <b>Отзывы</b>\n\n"
        f"Всего: {len(reviews)}\n"
        f"Выберите отзыв:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer()

@router.callback_query(F.data.startswith("new_report_page_"))
async def new_reports_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    page = int(callback.data.split("_")[-1])
    reports = await get_reports(status='new')
    
    total_pages = math.ceil(len(reports) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        reports, 
        page, 
        total_pages, 
        "new_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} ({r['danger_level']})"
    )
    
    await callback.message.edit_text(
        f"📋 <b>Новые отчёты</b>\n\n"
        f"Всего: {len(reports)}\n"
        f"Страница {page+1}/{total_pages}\n"
        f"Выберите отчёт для просмотра:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("new_report_") & ~F.data.contains("page"))
async def show_new_report_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    report_id = int(callback.data.split("_")[-1])
    reports = await get_reports()
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        await callback.answer("❌ Отчёт не найден", show_alert=True)
        return
    
    photo_path = os.path.join('uploads', report['photo_path'])
    
    text = (
        f"📋 <b>Отчёт #{report['id']}</b>\n\n"
        f"👤 Пользователь: @{report.get('username', 'Неизвестно')}\n"
        f"🗑 Тип отходов: {report['waste_type']}\n"
        f"⚠️ Опасность: {report['danger_level']}\n"
        f"📍 Координаты: {report['latitude']}, {report['longitude']}\n"
        f"📝 Описание: {report['description']}\n"
        f"📅 Дата: {report['created_at'][:16]}"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ На рассмотрении", callback_data=f"status_{report_id}_reviewing"),
                InlineKeyboardButton(text="🔧 В работе", callback_data=f"status_{report_id}_in_progress")
            ],
            [
                InlineKeyboardButton(text="✔️ Решено", callback_data=f"status_{report_id}_resolved"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status_{report_id}_rejected")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{report_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_new")
            ]
        ]
    )
    
    try:
        photo_file = FSInputFile(photo_path)
        await callback.message.answer_photo(
            photo=photo_file,
            caption=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer(
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        try:
            await callback.message.delete()
        except:
            pass
    
    await callback.answer()

@router.callback_query(F.data == "back_to_new")
async def back_to_new_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    reports = await get_reports(status='new')
    
    if not reports:
        await callback.message.answer("📋 Нет новых отчётов")
        await callback.answer()
        return
    
    total_pages = math.ceil(len(reports) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        reports, 
        0, 
        total_pages, 
        "new_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} ({r['danger_level']})"
    )
    
    await callback.message.answer(
        f"📋 <b>Новые отчёты</b>\n\n"
        f"Всего: {len(reports)}\n"
        f"Выберите отчёт для просмотра:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.answer()

@router.message(F.text == "🔍 Нерешённые отчёты")
async def show_unsolved_reports(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    all_reports = await get_reports()
    unsolved = [r for r in all_reports if r['status'] != 'resolved']
    
    if not unsolved:
        await message.answer("📋 Нет нерешённых отчётов")
        return
    
    total_pages = math.ceil(len(unsolved) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        unsolved, 
        0, 
        total_pages, 
        "unsolved_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} | {get_status_emoji(r['status'])}"
    )
    
    await message.answer(
        f"📋 <b>Нерешённые отчёты</b>\n\n"
        f"Всего: {len(unsolved)}\n"
        f"Выберите отчёт для редактирования:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("unsolved_report_page_"))
async def unsolved_reports_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    page = int(callback.data.split("_")[-1])
    all_reports = await get_reports()
    unsolved = [r for r in all_reports if r['status'] != 'resolved']
    
    total_pages = math.ceil(len(unsolved) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        unsolved, 
        page, 
        total_pages, 
        "unsolved_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} | {get_status_emoji(r['status'])}"
    )
    
    await callback.message.edit_text(
        f"📋 <b>Нерешённые отчёты</b>\n\n"
        f"Всего: {len(unsolved)}\n"
        f"Страница {page+1}/{total_pages}\n"
        f"Выберите отчёт для редактирования:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("unsolved_report_") & ~F.data.contains("page"))
async def show_unsolved_report_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    report_id = int(callback.data.split("_")[-1])
    reports = await get_reports()
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        await callback.answer("❌ Отчёт не найден", show_alert=True)
        return
    
    photo_path = os.path.join('uploads', report['photo_path'])
    
    text = (
        f"📋 <b>Отчёт #{report['id']}</b>\n\n"
        f"👤 Пользователь: @{report.get('username', 'Неизвестно')}\n"
        f"🗑 Тип отходов: {report['waste_type']}\n"
        f"⚠️ Опасность: {report['danger_level']}\n"
        f"📊 Статус: {get_status_name(report['status'])}\n"
        f"📍 Координаты: {report['latitude']}, {report['longitude']}\n"
        f"📝 Описание: {report['description']}\n"
        f"📅 Дата: {report['created_at'][:16]}"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ На рассмотрении", callback_data=f"status_{report_id}_reviewing"),
                InlineKeyboardButton(text="🔧 В работе", callback_data=f"status_{report_id}_in_progress")
            ],
            [
                InlineKeyboardButton(text="✔️ Решить", callback_data=f"status_{report_id}_resolved"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status_{report_id}_rejected")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{report_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_unsolved")
            ]
        ]
    )
    
    try:
        photo_file = FSInputFile(photo_path)
        await callback.message.answer_photo(
            photo=photo_file,
            caption=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        await callback.message.delete()
    except:
        await callback.message.answer(
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        try:
            await callback.message.delete()
        except:
            pass
    
    await callback.answer()

@router.callback_query(F.data == "back_to_unsolved")
async def back_to_unsolved_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    all_reports = await get_reports()
    unsolved = [r for r in all_reports if r['status'] != 'resolved']
    
    if not unsolved:
        await callback.message.answer("📋 Нет нерешённых отчётов")
        await callback.answer()
        return
    
    total_pages = math.ceil(len(unsolved) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        unsolved, 
        0, 
        total_pages, 
        "unsolved_report",
        lambda r: f"📋 #{r['id']} - {r['waste_type']} | {get_status_emoji(r['status'])}"
    )
    
    await callback.message.answer(
        f"📋 <b>Нерешённые отчёты</b>\n\n"
        f"Всего: {len(unsolved)}\n"
        f"Выберите отчёт для редактирования:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.answer()

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
    
    reports = await get_reports()
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if report:
        try:
            await callback.bot.send_message(
                report['user_id'],
                f"🔔 <b>Статус вашего отчёта изменён!</b>\n\n"
                f"📋 Отчёт #{report_id}\n"
                f"🗑 Тип: {report['waste_type']}\n"
                f"📊 Новый статус: {status_names[new_status]}\n\n"
                f"Спасибо за вашу бдительность! 🌍",
                parse_mode='HTML'
            )
        except:
            pass
    
    await callback.answer(
        f"✅ Статус изменён на: {status_names[new_status]}",
        show_alert=True
    )
    
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(F.data.startswith("delete_"))
async def delete_report_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    report_id = int(callback.data.split("_")[1])
    
    await delete_report(report_id)
    
    await callback.answer("🗑 Отчёт удалён", show_alert=True)
    
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "📊 Статистика")
async def show_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    import aiohttp
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{backend_url}/api/stats') as response:
            if response.status != 200:
                await message.answer("❌ Ошибка получения статистики")
                return
            
            stats = await response.json()
    
    text = (
        f"📊 <b>Общая статистика</b>\n\n"
        f"📝 Всего отчётов: {stats['total_reports']}\n"
        f"👥 Всего пользователей: {stats['total_users']}\n\n"
        f"<b>По статусам:</b>\n"
    )
    
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
    
    for status, count in stats['reports_by_status'].items():
        text += f"{status_emoji[status]} {status_names[status]}: {count}\n"
    
    text += "\n<b>По типам отходов:</b>\n"
    for waste_type, count in stats['reports_by_type'].items():
        text += f"• {waste_type}: {count}\n"
    
    await message.answer(text, parse_mode='HTML')

@router.message(F.text == "👥 Пользователи")
async def show_users_list(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    db.connect(reuse_if_open=True)
    users = list(User.select().order_by(User.rating.desc()))
    db.close()
    
    if not users:
        await message.answer("👥 Нет пользователей")
        return
    
    total_pages = math.ceil(len(users) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        users, 
        0, 
        total_pages, 
        "user",
        lambda u: f"👤 @{u.username or 'Неизвестно'} | {u.reports_count} отчётов | {u.rating} ⭐"
    )
    
    await message.answer(
        f"👥 <b>Пользователи</b>\n\n"
        f"Всего: {len(users)}\n"
        f"Выберите пользователя:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("user_page_"))
async def users_page(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    page = int(callback.data.split("_")[-1])
    
    db.connect(reuse_if_open=True)
    users = list(User.select().order_by(User.rating.desc()))
    db.close()
    
    total_pages = math.ceil(len(users) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        users, 
        page, 
        total_pages, 
        "user",
        lambda u: f"👤 @{u.username or 'Неизвестно'} | {u.reports_count} отчётов | {u.rating} ⭐"
    )
    
    await callback.message.edit_text(
        f"👥 <b>Пользователи</b>\n\n"
        f"Всего: {len(users)}\n"
        f"Страница {page+1}/{total_pages}\n"
        f"Выберите пользователя:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_") & ~F.data.contains("page"))
async def show_user_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    db.connect(reuse_if_open=True)
    try:
        user = User.get_by_id(user_id)
    except:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        db.close()
        return
    
    reports = list(user.reports)
    db.close()
    
    reports_by_status = {}
    for report in reports:
        status = report.status
        reports_by_status[status] = reports_by_status.get(status, 0) + 1
    
    text = (
        f"👤 <b>Профиль пользователя</b>\n\n"
        f"ID: {user.telegram_id}\n"
        f"Username: @{user.username or 'Неизвестно'}\n"
        f"Имя: {user.first_name or 'Не указано'}\n"
        f"📝 Отчётов: {user.reports_count}\n"
        f"⭐ Рейтинг: {user.rating}\n"
        f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        f"<b>Отчёты по статусам:</b>\n"
    )
    
    status_names = {
        'new': '🆕 Новые',
        'reviewing': '👀 На рассмотрении',
        'in_progress': '🔧 В работе',
        'resolved': '✅ Решённые',
        'rejected': '❌ Отклонённые'
    }
    
    for status, count in reports_by_status.items():
        text += f"{status_names.get(status, status)}: {count}\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_users")]
        ]
    )
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_users")
async def back_to_users_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    db.connect(reuse_if_open=True)
    users = list(User.select().order_by(User.rating.desc()))
    db.close()
    
    if not users:
        await callback.message.answer("👥 Нет пользователей")
        await callback.answer()
        return
    
    total_pages = math.ceil(len(users) / ITEMS_PER_PAGE)
    
    keyboard = create_pagination_keyboard(
        users, 
        0, 
        total_pages, 
        "user",
        lambda u: f"👤 @{u.username or 'Неизвестно'} | {u.reports_count} отчётов | {u.rating} ⭐"
    )
    
    await callback.message.answer(
        f"👥 <b>Пользователи</b>\n\n"
        f"Всего: {len(users)}\n"
        f"Выберите пользователя:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.answer()

@router.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(callback: CallbackQuery):
    await callback.message.answer(
        "👨‍💼 Админ-панель",
        reply_markup=admin_menu_keyboard()
    )
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()

def get_status_emoji(status):
    emoji_map = {
        'new': '🆕',
        'reviewing': '👀',
        'in_progress': '🔧',
        'resolved': '✅',
        'rejected': '❌'
    }
    return emoji_map.get(status, '❓')

def get_status_name(status):
    names = {
        'new': 'Новый',
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решён',
        'rejected': 'Отклонён'
    }
    return names.get(status, status)