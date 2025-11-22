from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Отправить отчёт")],
            [KeyboardButton(text="📊 Моя статистика"), KeyboardButton(text="🗺 Карта загрязнений")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def admin_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Новые отчёты"), KeyboardButton(text="🔍 Все отчёты")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="🔙 Выйти из админки")]
        ],
        resize_keyboard=True
    )
    return keyboard

def location_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="✍️ Ввести адрес вручную")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def report_status_keyboard(report_id):
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
            ]
        ]
    )
    return keyboard

def pagination_keyboard(page, total_pages, prefix):
    buttons = []
    
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}_page_{page+1}"))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard
