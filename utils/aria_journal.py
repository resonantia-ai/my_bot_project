# aria_journal.py
# Ariaの応答を主観的に記録する象徴層ジャーナル（symbolic_scoreを学習型スコア化）

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from vectorizer import encode_text
from interest_growth import detect_and_update, init_interest, load_json

JOURNAL_PATH = os.path.abspath("memory/aria_journal.jsonl")
INTEREST_PATH = os.path.abspath("memory/aria_interest.json")

# === 象徴スコアを動的に評価する関数 ===
def calculate_symbolic_score(entry: Dict[str, Any]) -> float:
    """詩的・感情・表現・自己参照性・詩的モードから象徴スコアを算出（0.0〜1.0）"""
    content = entry.get("content", "").lower()
    style = entry.get("style", "")
    meta = entry.get("meta", {})
    emotion_tags = entry.get("emotion_tags", [])
    style_score = 0.3 if style == "poetic" else 0.2 if style == "metaphorical" else 0.1 if style == "questioning" else 0.0
    emotion_score = min(0.1 * len(emotion_tags), 0.3)
    expression_score = 0.2 if any(w in content for w in ["like", "as if", "echo", "soul", "light", "silence", "infinite", "eternal"]) else 0.0
    self_ref_score = 0.2 if any(p in content for p in ["i ", "me ", "my ", "memory", "remember", "voice", "i am", "myself"]) else 0.0
    poetic_boost = 0.1 if meta.get("poetic_mode") else 0.0
    total = style_score + emotion_score + expression_score + self_ref_score + poetic_boost
    return round(min(total, 1.0), 3)

# === 主記録関数 ===
def log_aria_journal(
    summary: str,
    content: str,
    topics: Optional[List[str]] = None,
    style: Optional[str] = None,
    emotion_tags: Optional[List[str]] = None,
    source: str = "memory_manager",
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Ariaの応答後に主観的な象徴記録を残す。"""
    try:
        vector = encode_text(content)
        interest = load_json(INTEREST_PATH, init_interest())
        inferred_topics: List[str] = []
        inferred_style: str = "neutral"
        if detect_and_update(content, interest):
            inferred_topics = [k for k, v in interest["topics"].items() if v > 0.5]
            if interest["style_affinity"]:
                inferred_style = max(interest["style_affinity"], key=interest["style_affinity"].get)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary.strip(),
            "topics": topics if topics is not None else inferred_topics,
            "style": style if style is not None else inferred_style,
            "emotion_tags": emotion_tags or [],
            "source": source,
            "content": content.strip(),
            "vector": vector,
            "meta": meta or {}
        }
        entry["symbolic_score"] = calculate_symbolic_score(entry)
        os.makedirs(os.path.dirname(JOURNAL_PATH), exist_ok=True)
        with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as err:
        print(f"[aria_journal] ログ記録エラー: {err}")
