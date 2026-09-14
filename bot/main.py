import os
import asyncio
from dotenv import load_dotenv
from database.db import init_db
from bot.client import DayZStoreBot

load_dotenv()

async def main():
    init_db()
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token or token == "SEU_DISCORD_BOT_TOKEN_AQUI":
        print("⚠️ DISCORD_BOT_TOKEN não configurado no arquivo .env")
        print("💡 Para ativar o bot em seu servidor real do Discord, insira o Token no .env e inicie novamente.")
        return

    bot = DayZStoreBot()
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
