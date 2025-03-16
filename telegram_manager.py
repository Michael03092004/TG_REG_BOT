import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
import os
import asyncio
import re

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")
LAST_UPDATE = os.getenv("LAST_UPDATE")

if not API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN not set in .env")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Dictionary for tracking user states
USER_STATE = {}


# /start command handler
@dp.message(Command(commands=["start"]))
async def send_welcome(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/bots") as resp:
            if resp.status == 200:
                result = await resp.json()
                bots_list = result.get("bots", {})

                if not bots_list:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text="You have no bots for now 🚀\n"
                             "To create your first bot, use /create"
                    )
                else:
                    for bot_name in bots_list.keys():
                        async with session.post(f"{BACKEND_URL}/manage_bot",
                                                json={"bot_name": bot_name, "action": "start"}):
                            pass
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text="✅ All bots are started!"
                    )
            else:
                await bot.send_message(chat_id=message.chat.id, text="Server error. Please try again later.")


# /update command handler
@dp.message(Command(commands=["update"]))
async def send_last_update(message: types.Message):
    if LAST_UPDATE:
        await bot.send_message(chat_id=message.chat.id, text=f"Last update: {LAST_UPDATE}")


# /bots command handler
@dp.message(Command(commands=["bots"]))
async def send_bots_list(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/bots") as resp:
            if resp.status == 200:
                result = await resp.json()
                bots_list = result.get("bots", {})
                if bots_list:
                    bots_text = "Bots list:\n" + "\n".join(
                        f"{name}: {status}" for name, status in bots_list.items()
                    )
                    await bot.send_message(chat_id=message.chat.id, text=bots_text)
                else:
                    await bot.send_message(chat_id=message.chat.id, text="No bots found")
            else:
                await bot.send_message(chat_id=message.chat.id, text=f"Server error: {resp.status}")


# /create command handler
@dp.message(Command(commands=["create"]))
async def create_bot(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/available_platforms") as resp:
            if resp.status == 200:
                result = await resp.json()
                platforms = result.get("platforms", [])

                if not platforms:
                    await bot.send_message(chat_id=message.chat.id, text=f"No available platforms for bot creation")
                    return

                # Save available platforms in user state
                user_id = message.from_user.id
                USER_STATE[user_id] = {"step": "awaiting_platform", "platforms": platforms}

                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=str(i + 1)) for i in range(len(platforms))]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )

                platform_list = "\n".join([f"{i + 1}. {platform}" for i, platform in enumerate(platforms)])
                await bot.send_message(chat_id=message.chat.id,
                                       text=f"Select a platform to create a bot:\n{platform_list}",
                                       reply_markup=keyboard)

            else:
                await bot.send_message(chat_id=message.chat.id, text="Server error while retrieving platform list.")


# Process platform selection
@dp.message(lambda message: message.text.isdigit() and USER_STATE.get(message.from_user.id, {}).get("step") == "awaiting_platform")
async def process_create_platform(message: types.Message):
    user_id = message.from_user.id
    platform_number = int(message.text) - 1  # Convert text to index

    if user_id not in USER_STATE or USER_STATE[user_id]["step"] != "awaiting_platform":
        return

    platforms = USER_STATE[user_id]["platforms"]

    if 0 <= platform_number < len(platforms):
        platform = platforms[platform_number]
        USER_STATE[user_id] = {"step": "awaiting_phone", "platform": platform}  # Обновляем состояние

        if platform.lower() == "telegram":
            await bot.send_message(chat_id=message.chat.id,
                                   text="Please enter the phone number in international format (+123456789):",
                                   reply_markup=ReplyKeyboardRemove())
        else:
            await bot.send_message(chat_id=message.chat.id, text=f"Setup for {platform} is not implemented yet.")
    else:
        await bot.send_message(chat_id=message.chat.id, text="Invalid selection. Please choose a valid number.")


# Handle phone number input
@dp.message(lambda message: USER_STATE.get(message.from_user.id, {}).get("step") == "awaiting_phone")
async def process_phone_number(message: types.Message):
    user_id = message.from_user.id
    phone_number = message.text

    if re.fullmatch(r"\+\d{7,15}", phone_number):
        USER_STATE[user_id]["step"] = "awaiting_code"
        USER_STATE[user_id]["phone"] = phone_number
        await bot.send_message(chat_id=message.chat.id, text="Enter the verification code sent to your Telegram:")

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BACKEND_URL}/create_telegram_bot", json={"phone_number": phone_number}) as resp:
                if resp.status == 200:
                    await bot.send_message(chat_id=message.chat.id, text="✅ Bot created and authorized. Please check your Telegram for the verification code.")
                elif resp.status == 409:
                    await bot.send_message(chat_id=message.chat.id, text="✅ Bot already exists. Please enter the verification code.")
                else:
                    await bot.send_message(chat_id=message.chat.id, text="❌ Error creating or authorizing bot. Please try again.")

    else:
        await bot.send_message(chat_id=message.chat.id, text="❌ Invalid phone number format! Please enter a valid international number (e.g., +123456789).")


# Handle verification code input
@dp.message(lambda message: USER_STATE.get(message.from_user.id, {}).get("step") == "awaiting_code")
async def process_verification_code(message: types.Message):
    user_id = message.from_user.id
    verification_code = message.text
    phone_number = USER_STATE[user_id].get("phone")

    if not phone_number:
        await bot.send_message(chat_id=message.chat.id, text="❌ Session expired. Please restart the process using /create")
        USER_STATE.pop(user_id, None)
        return

    if not re.fullmatch(r"\d{4,6}", verification_code):
        await bot.send_message(chat_id=message.chat.id, text="❌ Invalid code format! Enter a 4-6 digit code.")
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/verify_telegram_bot", json={
            "phone_number": phone_number,
            "verification_code": verification_code
        }) as resp:
            if resp.status == 200:
                USER_STATE.pop(user_id, None)
                await bot.send_message(chat_id=message.chat.id, text="✅ Telegram bot verified successfully!")
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{BACKEND_URL}/search_groups", json={
                        "phone_number": phone_number,
                        "keyword": "Шукаю роботу"
                    }) as resp:
                        if resp.status == 200:
                            return
            elif resp.status == 400:
                await bot.send_message(chat_id=message.chat.id, text="❌ Incorrect verification code. Please try again.")
            elif resp.status == 429:
                await bot.send_message(chat_id=message.chat.id, text="⚠️ Too many attempts. Please wait and try again later.")
            else:
                await bot.send_message(chat_id=message.chat.id, text="❌ Error verifying bot. Please try again later.")


async def main():
    try:
        print("Telegram Manager Bot started")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

asyncio.run(main())