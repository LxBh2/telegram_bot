import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

from config import TOKEN, ADMIN_ID
from db import init_db, save_application, get_applications
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


class Form(StatesGroup):
    name = State()
    age = State()
    contact = State()
    instagram = State()
    telegram = State()
    text = State()

# START
@router.message(F.text == "/start")
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start_form")]
    ])

    await message.answer(
        "Бот для подачи заявки. Нажми «Начать».",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "start_form")
async def start_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.name)
    await callback.message.answer("Напиши своё имя:")
    await callback.answer()
    
# NAME
@router.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Сколько тебе лет?")


# AGE
@router.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.contact)
    await message.answer("Контакт (телефон или email):")


# CONTACT
@router.message(Form.contact)
async def contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Form.instagram)
    await message.answer("Instagram (если есть):")


# INSTAGRAM
@router.message(Form.instagram)
async def instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text)
    await state.set_state(Form.telegram)
    await message.answer("Telegram:")


# TELEGRAM
@router.message(Form.telegram)
async def telegram_step(message: Message, state: FSMContext):
    await state.update_data(telegram=message.text)
    await state.set_state(Form.text)
    await message.answer("Текст заявки:")


# FINAL
@router.message(Form.text)
async def final(message: Message, state: FSMContext):
    data = await state.get_data()

    await save_application(data, message.text)

    text = (
        f"🔔 <b>Новая заявка</b>\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"🎂 Возраст: {data.get('age')}\n"
        f"📞 Контакт: {data.get('contact')}\n"
        f"📸 Instagram: {data.get('instagram')}\n"
        f"✈️ Telegram: {data.get('telegram')}\n\n"
        f"📝 Текст:\n{message.text}"
    )

    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except TelegramBadRequest as e:
        print("Ошибка отправки админу:", e)

    await message.answer("Заявка отправлена")
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Заполнить ещё раз", callback_data="start_form")]
])


@router.message(F.text == "/applications")
async def applications(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    rows = await get_applications(10)

    if not rows:
        await message.answer("Заявок нет")
        return

    for r in rows:
        await message.answer(
            f"🆔 {r['id']}\n"
            f"👤 {r['name']} ({r['age']})\n"
            f"📞 {r['contact']}\n"
            f"📸 {r['instagram']}\n"
            f"✈️ {r['telegram']}\n\n"
            f"📝 {r['application_text']}"
        )

async def main():
    await init_db()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())