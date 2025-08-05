# english_bot.py
# Aria構文人格を用いた統合Bot本体


import os
import re
import time
import subprocess
import json
import requests
import discord
from discord.ext import commands
from typing import Set, Dict, Any, List

# ベクトル初期化（起動時に一括処理）
subprocess.run(["python", os.path.abspath("utils/vectorizer.py")], check=True)

from dotenv import load_dotenv
from memory_manager import build_prompt

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LM_API_URL = os.getenv("LM_API_URL")

PROMPT_PATH = os.path.abspath("aria_prompt.txt")

# === Aria人格プロンプト読み込み ===
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

IGNORE_USER_IDS: Set[int] = set()
recent_messages: Dict[str, float] = {}

# === 英文比率で判定 ===
def is_majority_english(text: str) -> bool:
    cleaned = re.sub(r"[^\w\s]", "", text)
    letters = [c for c in cleaned if c.isalpha()]
    if not letters:
        return False
    english = sum(1 for c in letters if c.lower() in "abcdefghijklmnopqrstuvwxyz")
    return english / len(letters) >= 0.5

# === 長文分割送信 ===
def split_message(text: str, max_length: int = 2000) -> List[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

@bot.event
async def on_ready():
    global IGNORE_USER_IDS
    IGNORE_USER_IDS = {bot.user.id}
    print(f"✅ AriaBot is online: {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    if message.author.id in IGNORE_USER_IDS:
        return

    content = message.content.strip()
    if not content or not is_majority_english(content):
        return

    now = time.time()
    if content in recent_messages and now - recent_messages[content] < 10:
        return
    recent_messages[content] = now

    # 🔁 プロンプト構築（memory_manager + 全構文）
    try:
        prompt = build_prompt(SYSTEM_PROMPT, content)
    except Exception as e:
        await message.channel.send(f"❌ Prompt build error: {str(e)}")
        print(f"Prompt build error: {e}")
        return

    payload = {
        "messages": prompt,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(LM_API_URL, json=payload)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()

        for chunk in split_message(reply):
            await message.channel.send(chunk)

        # ベクトル記録（非同期追記）
        cleaned_reply = reply.replace("\n", " ").replace('"', "'").strip()
        subprocess.Popen(["python", os.path.abspath("utils/vectorizer.py"), "--mode", "append", cleaned_reply])

    except Exception as e:
        await message.channel.send(f"❌ Error: {str(e)}")
        print(f"Error: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
