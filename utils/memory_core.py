# memory_core.py


import os
import json
import uuid
from datetime import datetime
from typing import List, Optional

# ファイルパス定義（絶対パス化）
MEMORY_DIR = os.path.abspath("memory")
DIALOG_LOG = os.path.join(MEMORY_DIR, "dialog_log.jsonl")
EMOTION_LOG = os.path.join(MEMORY_DIR, "emotion_vec.json")
SHORT_TERM = os.path.join(MEMORY_DIR, "short_term_memory.json")
LONG_TERM = os.path.join(MEMORY_DIR, "compressed_memory.json")
TTL_HALF_LIFE = 60 * 60 * 24 * 3  # 3日

# === ダイアログと感情ログ ===
def log_dialog(
    user_text: str,
    bot_text: str,
    emotion_tags: Optional[List[str]] = None,
    topic: Optional[str] = None
) -> None:
    """
    ユーザーとBotの対話・感情を記録する
    """
    now = datetime.now().isoformat()
    uid = str(uuid.uuid4())[:8]
    os.makedirs(MEMORY_DIR, exist_ok=True)
    entry = {
        "id": uid,
        "timestamp": now,
        "user": user_text,
        "aria": bot_text,
        "topic": topic or ""
    }
    try:
        with open(DIALOG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[memory_core] ダイアログ記録エラー: {e}")

    if emotion_tags:
        vec = {tag: 1.0 for tag in emotion_tags}
        vec["timestamp"] = now
        try:
            with open(EMOTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(vec, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[memory_core] 感情記録エラー: {e}")

# === トークン数上限内で短期記憶を抽出し、残りを長期記憶化 ===
def trim_memory(max_tokens: int = 2000) -> None:
    """
    トークン数上限内で短期記憶を抽出し、残りを長期記憶化
    """
    if not os.path.exists(DIALOG_LOG):
        return
    try:
        with open(DIALOG_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[memory_core] ダイアログ読込エラー: {e}")
        return

    short_term, long_term = [], []
    token_count = 0

    for line in reversed(lines):
        try:
            entry = json.loads(line)
            user = entry.get("user", "")
            aria = entry.get("aria", "")
            tokens = len(user) + len(aria)
            if token_count + tokens <= max_tokens:
                short_term.insert(0, {"role": "user", "content": user})
                short_term.append({"role": "assistant", "content": aria})
                token_count += tokens
            else:
                long_term.insert(0, {
                    "id": entry.get("id", ""),
                    "content": f"{user} / {aria}",
                    "timestamp": entry.get("timestamp"),
                    "topic": entry.get("topic", "")
                })
        except Exception as e:
            print(f"[memory_core] 記憶分割エラー: {e}")
            continue

    try:
        with open(SHORT_TERM, "w", encoding="utf-8") as f:
            json.dump(short_term, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[memory_core] 短期記憶保存エラー: {e}")

    if long_term:
        existing = []
        if os.path.exists(LONG_TERM):
            try:
                with open(LONG_TERM, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception as e:
                print(f"[memory_core] 長期記憶読込エラー: {e}")
        combined = existing + long_term
        try:
            with open(LONG_TERM, "w", encoding="utf-8") as f:
                json.dump(combined, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[memory_core] 長期記憶保存エラー: {e}")

    print(f"✅ 記憶更新：短期={len(short_term)}件、長期追加={len(long_term)}件")
