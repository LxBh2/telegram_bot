import asyncio
from aiogram.filters import StateFilter
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


@router.message(F.text == "/start")
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Start", callback_data="start_form")]
    ])

    await message.answer(
        'Bot for submitting an application. Click "Start".',
        reply_markup=keyboard
    )

@router.callback_query(F.data == "start_form")
async def start_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.name)
    await callback.message.answer("Enter your name:")
    await callback.answer()


@router.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("How old are you?")



@router.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Form.contact)
    await message.answer("Contact (phone or email):")



@router.message(Form.contact)
async def contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Form.instagram)
    await message.answer("Instagram (if any):")



@router.message(Form.instagram)
async def instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text)
    await state.set_state(Form.telegram)
    await message.answer("Telegram (if any):")



@router.message(Form.telegram)
async def telegram_step(message: Message, state: FSMContext):
    await state.update_data(telegram=message.text)
    await state.set_state(Form.text)
    await message.answer("Application Text")


@router.message(Form.text)
async def final(message: Message, state: FSMContext):
    data = await state.get_data()

    await save_application(data, message.text)

    text = (
        f"🔔 <b>New Resume</b>\n\n"
        f"👤 Name: {data.get('name')}\n"
        f"🎂 Age: {data.get('age')}\n"
        f"📞 Contact: {data.get('contact')}\n"
        f"📸 Instagram: {data.get('instagram')}\n"
        f"✈️ Telegram: {data.get('telegram')}\n\n"
        f"📝 Resume:\n{message.text}"
    )

    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except TelegramBadRequest as e:
        print("Error sending to admin:", e)

    await message.answer("The application has been sent.")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Fill it out again", callback_data="start_form")]
    ])

    await message.answer("If you'd like to submit another application, click below.", reply_markup=keyboard)

@router.message(StateFilter("*"), F.text == "/applications")
async def applications(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()

    print("Fetching applications...")  

    rows = await get_applications(10)

    print("Rows:", rows)  

    if not rows:
        await message.answer("No applications")
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