from aiogram import Router, F
from aiogram.types import Message, Location, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import location_keyboard, main_menu_keyboard, cancel_keyboard
from bot.utils import extract_gps_from_image, create_report, get_coordinates_from_address
from backend.services import gigachat_service
import os
import uuid

router = Router()

class ReportStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_address = State()

@router.message(F.text == "📸 Отправить отчёт")
async def start_report(message: Message, state: FSMContext):
    await message.answer(
        "📸 Отправьте фотографию загрязнения.\n\n"
        "Вы можете:\n"
        "• Отправить фото напрямую\n"
        "• Отправить как файл (для сохранения метаданных GPS)\n\n"
        "Постарайтесь сфотографировать проблему чётко и с разных ракурсов.",
        reply_markup=cancel_keyboard()
    )

@router.message(F.text == "❌ Отмена")
async def cancel_report(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Отправка отчёта отменена.",
        reply_markup=main_menu_keyboard()
    )

@router.message(F.photo | F.document)
async def process_photo(message: Message, state: FSMContext):
    file_id = None
    file_path_in_bot = None
    
    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
    
    if not file_id:
        return
    
    file = await message.bot.get_file(file_id)
    file_path_in_bot = file.file_path
    
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join("uploads", filename)
    
    await message.bot.download_file(file_path_in_bot, filepath)
    
    await message.answer("🤖 Анализирую изображение...")
    
    analysis = gigachat_service.analyze_image(filepath)
    
    if not analysis or not analysis.get('is_pollution'):
        os.remove(filepath)
        await message.answer(
            "❌ На фото не обнаружено экологических загрязнений.\n\n"
            "Пожалуйста, отправьте фото со свалкой, мусором или другими загрязнениями.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return
    
    await message.answer(
        f"✅ Загрязнение обнаружено!\n\n"
        f"📋 Описание: {analysis.get('description')}\n"
        f"🗑 Тип отходов: {analysis.get('waste_type')}\n"
        f"⚠️ Уровень опасности: {analysis.get('danger_level')}\n"
        f"⭐️ За этот отчёт: +{analysis.get('rating_points', 10)} баллов"
    )
    
    gps = extract_gps_from_image(filepath)
    
    await state.update_data(
        photo_path=filename,
        description=analysis.get('description'),
        waste_type=analysis.get('waste_type'),
        danger_level=analysis.get('danger_level'),
        rating_points=analysis.get('rating_points', 10)
    )
    
    if gps:
        await state.update_data(
            latitude=gps['latitude'],
            longitude=gps['longitude']
        )
        
        data = await state.get_data()
        
        result = await create_report(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            photo_path=data['photo_path'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            address=None,
            description=data['description'],
            waste_type=data['waste_type'],
            danger_level=data['danger_level'],
            rating_points=data.get('rating_points', 10)
        )
        
        await message.answer(
            f"✅ Отчёт #{result['id']} успешно отправлен!\n\n"
            f"Ваш рейтинг увеличен на {data.get('rating_points', 10)} баллов! ⭐️",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
    else:
        await state.set_state(ReportStates.waiting_for_location)
        await message.answer(
            "📍 Геолокация не найдена в метаданных фото.\n\n"
            "Пожалуйста, отправьте геолокацию или введите адрес вручную.",
            reply_markup=location_keyboard()
        )

@router.message(ReportStates.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    location = message.location
    
    await state.update_data(
        latitude=location.latitude,
        longitude=location.longitude
    )
    
    data = await state.get_data()
    
    result = await create_report(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        photo_path=data['photo_path'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=None,
        description=data['description'],
        waste_type=data['waste_type'],
        danger_level=data['danger_level'],
        rating_points=data.get('rating_points', 10)
    )
    
    await message.answer(
        f"✅ Отчёт #{result['id']} успешно отправлен!\n\n"
        f"Ваш рейтинг увеличен на {data.get('rating_points', 10)} баллов! ⭐️",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

@router.message(ReportStates.waiting_for_location, F.text == "✍️ Ввести адрес вручную")
async def ask_for_address(message: Message, state: FSMContext):
    await state.set_state(ReportStates.waiting_for_address)
    await message.answer(
        "✍️ Введите адрес загрязнения:",
        reply_markup=cancel_keyboard()
    )

@router.message(ReportStates.waiting_for_address, F.text)
async def process_address(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_report(message, state)
        return
    
    address = message.text
    
    coords = await get_coordinates_from_address(address)
    
    if not coords:
        await message.answer(
            "❌ Не удалось найти координаты по этому адресу.\n\n"
            "Попробуйте ввести адрес по-другому или отправьте геолокацию.",
            reply_markup=location_keyboard()
        )
        return
    
    await state.update_data(
        address=address,
        latitude=coords['latitude'],
        longitude=coords['longitude']
    )
    
    data = await state.get_data()
    
    result = await create_report(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        photo_path=data['photo_path'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data['address'],
        description=data['description'],
        waste_type=data['waste_type'],
        danger_level=data['danger_level'],
        rating_points=data.get('rating_points', 10)
    )
    
    await message.answer(
        f"✅ Отчёт #{result['id']} успешно отправлен!\n\n"
        f"📍 Адрес: {address}\n"
        f"Ваш рейтинг увеличен на {data.get('rating_points', 10)} баллов! ⭐️",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "🗺 Карта загрязнений")
async def show_map(message: Message):
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    
    await message.answer(
        "🗺 Карта всех загрязнений:\n\n"
        f"<a href='{backend_url}'>Откройте карту в браузере</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Как отправить отчёт:</b>\n"
        "1. Сфотографируйте загрязнение\n"
        "2. Отправьте фото боту (можно прямо в чат или как файл)\n"
        "3. Бот автоматически определит тип отходов и опасность\n"
        "4. Если в фото есть геолокация - отчёт отправится автоматически\n"
        "5. Если нет - отправьте геолокацию или введите адрес\n\n"
        "<b>Рейтинг:</b>\n"
        "За каждый отчёт вы получаете от 5 до 30 баллов в зависимости от серьёзности загрязнения\n\n"
        "<b>Статусы отчётов:</b>\n"
        "🆕 Новый - только что создан\n"
        "👀 На рассмотрении - принят к рассмотрению\n"
        "🔧 В работе - проблема решается\n"
        "✅ Решён - проблема устранена\n"
        "❌ Отклонён - не является загрязнением",
        parse_mode='HTML'
    )
