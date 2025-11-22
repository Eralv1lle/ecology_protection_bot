from aiogram import Router, F
from aiogram.types import Message, Location
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import location_keyboard, main_menu_keyboard, cancel_keyboard
from bot.utils import extract_gps_from_image, create_report
from backend.services import gigachat_service
import os
import uuid

router = Router()

class ReportStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_location = State()
    waiting_for_address = State()

@router.message(F.text == "📸 Отправить отчёт")
async def start_report(message: Message, state: FSMContext):
    await state.set_state(ReportStates.waiting_for_photo)
    await message.answer(
        "📸 Отправьте фотографию загрязнения.\n\n"
        "Постарайтесь сфотографировать проблему чётко, одной фотографией.",
        reply_markup=cancel_keyboard()
    )

@router.message(F.text == "❌ Отмена")
async def cancel_report(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Отправка отчёта отменена.",
        reply_markup=main_menu_keyboard()
    )

@router.message(ReportStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    
    file_id = photo.file_id
    file = await message.bot.get_file(file_id)

    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join("uploads", filename)

    await message.bot.download_file(file.file_path, filepath)
    
    await message.answer("🤖 Анализирую изображение...")
    
    analysis = gigachat_service.analyze_image(filepath)
    print(analysis)
    if not analysis or not analysis.get('is_pollution'):
        os.remove(filepath)
        await message.answer(
            "❌ На фото не обнаружено экологических загрязнений.\n\n"
            "Пожалуйста, отправьте фото со свалкой, мусором или другими загрязнениями.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return
    
    gps = extract_gps_from_image(filepath)
    
    await state.update_data(
        photo_path=filename,
        description=analysis.get('description'),
        waste_type=analysis.get('waste_type'),
        danger_level=analysis.get('danger_level')
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
            danger_level=data['danger_level']
        )
        
        await message.answer(
            f"✅ Отчёт успешно отправлен!\n\n"
            f"📋 Описание: {data['description']}\n"
            f"🗑 Тип отходов: {data['waste_type']}\n"
            f"⚠️ Уровень опасности: {data['danger_level']}\n\n"
            f"Ваш рейтинг увеличен на 10 баллов! ⭐️",
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
        danger_level=data['danger_level']
    )
    
    await message.answer(
        f"✅ Отчёт успешно отправлен!\n\n"
        f"📋 Описание: {data['description']}\n"
        f"🗑 Тип отходов: {data['waste_type']}\n"
        f"⚠️ Уровень опасности: {data['danger_level']}\n\n"
        f"Ваш рейтинг увеличен на 10 баллов! ⭐️",
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
    address = message.text
    
    await state.update_data(
        address=address,
        latitude=0.0,
        longitude=0.0
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
        danger_level=data['danger_level']
    )
    
    await message.answer(
        f"✅ Отчёт успешно отправлен!\n\n"
        f"📋 Описание: {data['description']}\n"
        f"🗑 Тип отходов: {data['waste_type']}\n"
        f"⚠️ Уровень опасности: {data['danger_level']}\n"
        f"📍 Адрес: {address}\n\n"
        f"Ваш рейтинг увеличен на 10 баллов! ⭐️",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "🗺 Карта загрязнений")
async def show_map(message: Message):
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    await message.answer(
        f"🗺 Карта всех загрязнений доступна на сайте:\n\n"
        f"{backend_url}\n\n"
        f"Там вы можете увидеть все отчёты и их статусы."
    )

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Как отправить отчёт:</b>\n"
        "1. Нажмите кнопку 'Отправить отчёт'\n"
        "2. Отправьте фото загрязнения\n"
        "3. Система автоматически определит тип отходов\n"
        "4. Если в фото есть геолокация - отчёт отправится автоматически\n"
        "5. Если нет - отправьте геолокацию или введите адрес\n\n"
        "<b>Рейтинг:</b>\n"
        "За каждый отчёт вы получаете +10 баллов рейтинга\n\n"
        "<b>Статусы отчётов:</b>\n"
        "🆕 Новый - только что создан\n"
        "👀 На рассмотрении - принят к рассмотрению\n"
        "🔧 В работе - проблема решается\n"
        "✅ Решён - проблема устранена\n"
        "❌ Отклонён - не является загрязнением",
        parse_mode='HTML'
    )
