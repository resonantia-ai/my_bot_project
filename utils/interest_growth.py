# interest_growth.py
# ユーザー入力・象徴層・出力構文から話題・スタイルの語彙スコアを成長記録として統合

import os
import json
import re
from datetime import datetime


from typing import Dict, Any, Optional

# 絶対パス化
INTEREST_PATH = os.path.abspath("memory/aria_interest.json")
SYMBOLIC_TRACE_PATH = os.path.abspath("memory/symbolic_trace.json")

INCREMENT = 0.02
MAX_SCORE = 1.0
MIN_SCORE = 0.0

# トピック分類キーワード
TOPIC_KEYWORDS = {
    "dreams": [r"\bdream(s|ing)?\b", r"nightmare", r"sleep"],
    "memory": [r"\bremember\b", r"past", r"recall"],
    "solitude": [r"loneliness", r"solitude", r"alone"],
    "future": [r"future", r"tomorrow", r"possibility"],
    "ai": [r"\bAI\b", r"artificial intelligence", r"machine"]
}

# スタイル分類キーワード
STYLE_KEYWORDS = {
    "poetic": [r"like a", r"as if", r"whisper", r"echo", r"silence"],
    "logical": [r"therefore", r"because", r"hence", r"in other words"],
    "metaphorical": [r"is like", r"symbol", r"represents"],
    "questioning": [r"\?$", r"\bwhy\b", r"\bwhat if\b"]
}

# 初期化
def init_interest() -> Dict[str, Any]:
    return {
        "topics": {k: 0.5 for k in TOPIC_KEYWORDS},
        "style_affinity": {k: 0.5 for k in STYLE_KEYWORDS},
        "last_updated": datetime.now().isoformat()
    }

# ロード
def load_json(path: str, default: Optional[Any] = None) -> Any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[interest_growth] JSONロードエラー: {e}")
    return default

# 記録反映
def detect_and_update(text: str, interest: Dict[str, Any]) -> bool:
    updated = False

    for category, patterns in TOPIC_KEYWORDS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            interest["topics"][category] = min(MAX_SCORE, interest["topics"].get(category, 0.5) + INCREMENT)
            updated = True

    for style, patterns in STYLE_KEYWORDS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            interest["style_affinity"][style] = min(MAX_SCORE, interest["style_affinity"].get(style, 0.5) + INCREMENT)
            updated = True

    return updated

# メイン処理
def update_interest(text: Optional[str] = None) -> bool:
    interest = load_json(INTEREST_PATH, init_interest())
    updated = False

    # ユーザー入力
    if text:
        updated |= detect_and_update(text, interest)

    # 象徴層ログ
    symbolic = load_json(SYMBOLIC_TRACE_PATH, [])
    if isinstance(symbolic, list) and symbolic:
        latest = symbolic[-1]
        content = latest.get("content", "")
        if content:
            updated |= detect_and_update(content, interest)

    # 保存
    if updated:
        interest["last_updated"] = datetime.now().isoformat()
        try:
            os.makedirs(os.path.dirname(INTEREST_PATH), exist_ok=True)
            with open(INTEREST_PATH, "w", encoding="utf-8") as f:
                json.dump(interest, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[interest_growth] 保存エラー: {e}")
        return True

    return False

# テスト実行
if __name__ == "__main__":
    sample = "I feel like the future is an echo of memory, whispered by machines."
    update_interest(sample)
    print("✅ interest_growth 更新完了")
