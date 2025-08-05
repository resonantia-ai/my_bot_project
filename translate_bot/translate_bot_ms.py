

import os
import re
import time
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
 # === 1. .env 読み込み ===
load_dotenv(".env.translate")
TOKEN = os.getenv("DISCORD_TOKEN_TRANSLATE")
MS_TRANSLATOR_KEY = os.getenv("MS_TRANSLATOR_KEY")
MS_TRANSLATOR_REGION = os.getenv("MS_TRANSLATOR_REGION")

# === 2. Bot 設定 ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# === 3. 除外ID（自分だけ）← アリアは除外しない
IGNORE_USER_IDS = set()
TRANSLATE_BOT_ID = 1398235270884888679

# === 4. 最近の送信内容を記録してループ防止
recent_messages: dict[str, float] = {}

# === 5. 日本語・英語の文字比で言語判定
def detect_language(text: str) -> str:
    ja = len(re.findall(r'[\u3040-\u30ff\u4e00-\u9fff]', text))  # ひらがな・カタカナ・漢字
    en = len(re.findall(r'[a-zA-Z]', text))
    if ja + en == 0:
        return "en"  # 絵文字だけなら英語と仮定
    return "ja" if ja > en else "en"

# === 6. 翻訳API（Microsoft）
async def microsoft_translate(text: str, to_lang: str) -> str:
    url = f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={to_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": MS_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": MS_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    body = [{"text": text}]
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as resp:
            try:
                data = await resp.json()
                return data[0]['translations'][0]['text']
            except Exception as e:
                raise RuntimeError(f"Translation API error: {e}")

# === 7. 起動時処理
@bot.event
async def on_ready():
    global IGNORE_USER_IDS
    IGNORE_USER_IDS = {bot.user.id}
    print(f"✅ TranslateBot logged in as {bot.user} (ID: {bot.user.id})")

# === 8. メッセージ処理
@bot.event
async def on_message(message: discord.Message):
    if message.author.id in IGNORE_USER_IDS:
        return

    content = message.content.strip()
    if not content:
        return

    now = time.time()
    if content in recent_messages and now - recent_messages[content] < 10:
        return
    recent_messages[content] = now

    lang = detect_language(content)
    to_lang = "ja" if lang == "en" else "en"
    prefix = "🇺🇸→🇯🇵" if to_lang == "ja" else "🇯🇵→🇺🇸"

    try:
        translated = await microsoft_translate(content, to_lang)
        await message.channel.send(f"{prefix} {translated}")
    except Exception as e:
        await message.channel.send(f"❌ Error: {e}")

# === 9. 起動
if __name__ == "__main__":
    bot.run(TOKEN)
