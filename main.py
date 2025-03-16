from fastapi import FastAPI
from api.endpoints import router
from bots.telegram_bot import TelegramBot
from contextlib import asynccontextmanager

app = FastAPI(title="HR Automation Backend")

# Словарь с экземплярами ботов
app.state.bots = {
    # "telegram": TelegramBot(bot_id="HR_M_official_bot"),
}

app.state.available_platforms = ["Telegram", "Instagram", "Facebook", "TikTok"]

app.include_router(router)

# Обработчик жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend started. Bots are ready to be managed.")
    yield
    print("Backend stopped.")

app.lifespan = lifespan

@app.get("/")
async def root():
    return {"message": "HR Automation Backend is running"}
