from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import main_menu_keyboard
import aiohttp
import os

router = Router()


class ReviewStates(StatesGroup):
    waiting_for_review = State()


@router.message(F.text == "⭐ Оставить отзыв")
async def start_review(message: Message, state: FSMContext):
    await state.set_state(ReviewStates.waiting_for_review)
    await message.answer(
        "⭐ <b>Оставить отзыв</b>\n\n"
        "Напишите ваш отзыв о нашем проекте.\n"
        "Расскажите, что вам понравилось или что можно улучшить:",
        parse_mode='HTML'
    )


@router.message(ReviewStates.waiting_for_review)
async def process_review(message: Message, state: FSMContext):
    review_text = message.text

    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')

    async with aiohttp.ClientSession() as session:
        async with session.post(f'{backend_url}/api/reviews', json={
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'text': review_text,
            'rating': 5
        }) as response:
            if response.status == 201:
                await message.answer(
                    "✅ Спасибо за ваш отзыв!\n\n"
                    "Ваш отзыв появится на нашем сайте.",
                    reply_markup=main_menu_keyboard()
                )
            else:
                await message.answer(
                    "❌ Ошибка при отправке отзыва. Попробуйте позже.",
                    reply_markup=main_menu_keyboard()
                )

    await state.clear()