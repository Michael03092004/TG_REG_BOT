from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from bots.base_bot import BaseBot
from bots.telegram_bot import TelegramBot

router = APIRouter()

class BotCommand(BaseModel):
    bot_name: str
    action: str  # "start", "stop", "status"

class TelegramLoginData(BaseModel):
    phone_number: str
    verification_code: str | None = None
    keyword: str | None = None

def get_bots(request: Request):
    return request.app.state.bots


@router.post("/manage_bot")
async def manage_bot(command: BotCommand, bots=Depends(get_bots)):
    bot: BaseBot = bots.get(command.bot_name)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if command.action == "start":
        await bot.start()
        return {"message": f"{command.bot_name} started"}
    elif command.action == "stop":
        await bot.stop()
        return {"message": f"{command.bot_name} stopped"}
    elif command.action == "status":
        return {"bot": command.bot_name, "status": bot.get_status()}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.get("/bots")
async def list_bots(request: Request):
    bots = request.app.state.bots
    return {"bots": {name: bot.get_status() for name, bot in bots.items()}}

@router.get("/available_platforms")
async def get_available_platforms(request: Request):
    platforms = request.app.state.available_platforms
    return {"platforms": platforms}


@router.post("/create_telegram_bot")
async def create_telegram_bot(data: TelegramLoginData, request: Request):
    bots = request.app.state.bots

    if data.phone_number in bots:
        raise HTTPException(status_code=400, detail="Telegram bot is already created. Please proceed to verification.")

    bot = TelegramBot(bot_id=data.phone_number)
    bots[data.phone_number] = bot

    await bot.create_bot(phone_number=data.phone_number)

    return {"message": "Telegram bot created. Please provide the verification code."}


@router.post("/verify_telegram_bot")
async def verify_telegram_bot(data: TelegramLoginData, request: Request):
    bots = request.app.state.bots

    bot = bots.get(data.phone_number)
    if not bot:
        raise HTTPException(status_code=404, detail="Telegram bot not found. Please create a bot first.")

    if not data.verification_code:
        raise HTTPException(status_code=400, detail="Verification code is required")

    await bot.verify_bot(verification_code=data.verification_code)

    return {"message": "Telegram bot successfully verified and logged in"}

@router.post("/search_groups")
async def search_groups(data: TelegramLoginData, request: Request):
    bots = request.app.state.bots

    bot = bots.get(data.phone_number)
    if not bot:
        raise HTTPException(status_code=404, detail="Telegram bot not found")

    await bot.search_groups(keyword=data.keyword)


