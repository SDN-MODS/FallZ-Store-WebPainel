import os
import sys
import asyncio

# Garante que o diretório raiz e o diretório pai estejam no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from dotenv import load_dotenv
from database.db import init_db
from bot.client import DayZStoreBot
from web.app import app

load_dotenv()

async def run_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token or token == "SEU_DISCORD_BOT_TOKEN_AQUI":
        print("⚠️ DISCORD_BOT_TOKEN não configurado no arquivo .env")
        print("💡 Insira o Token no .env ou nas Configurações do Painel Web para iniciar o Bot.")
        return

    max_retries = 5
    retry_delay = 5

    for attempt in range(1, max_retries + 1):
        bot = DayZStoreBot()
        try:
            print(f"🤖 Tentando conectar ao Discord (Tentativa {attempt}/{max_retries})...")
            async with bot:
                await bot.start(token)
            break
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ Erro ao conectar ao Gateway do Discord: {err_msg}")
            if "503" in err_msg or "Service Unavailable" in err_msg or "Invalid response status" in err_msg:
                print("🌐 Os servidores do Discord estão temporariamente indisponíveis (Erro 503 HTTP/Gateway).")
                print("💡 Isso ocorre quando a API do Discord está em manutenção ou enfrentando oscilação na conexão com a internet.")
            if attempt < max_retries:
                print(f"⏳ Aguardando {retry_delay} segundos antes de tentar reconectar novamente...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("❌ Não foi possível conectar ao Discord após várias tentativas.")

async def main():
    init_db()
    print("✓ Banco de dados inicializado com sucesso!")
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
