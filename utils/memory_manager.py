# memory_manager.py
# �S�L���w�Erag�E���w�E�ے��w�E���������𓝍����āA�\���v�����v�g�𐶐�


import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from symbolic_reflector import recall_symbolic_memories
from poetic_reflector import generate_poetic_reflection
from aria_journal import log_aria_journal  # �ǉ�

MEMORY_DIR = os.path.abspath("memory")

def load_json(path: str, fallback: Optional[Any] = None) -> Any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[memory_manager] JSONロードエラー: {e}")
    return fallback if fallback is not None else []

# ���S�g���~���O
def safe_trim(text: str, limit: int = 500) -> str:
    """
    指定文字数で安全にトリム（文末で切る）
    """
    return text if len(text) <= limit else text[:limit].rsplit(".", 1)[0] + "."

# === ���C���\���v�����v�g�\�z ===
def build_prompt(system_prompt: str, user_input: str) -> List[Dict[str, Any]]:
    """
    プロンプトを構築（短期記憶・象徴層・RAG・詩的反映を統合）
    """
    prompt: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # [1] 短期記憶
    memory = load_json(os.path.join(MEMORY_DIR, "short_term_memory.json"), [])
    prompt.extend(memory)

    # [2] 象徴層記憶
    reused = recall_symbolic_memories(user_input)
    for entry in reused:
        content = entry.get("content") or entry.get("text")
        if content:
            prompt.append({
                "role": "assistant",
                "content": f"[Symbolic Echo]\n{content}"
            })

    # [3] RAG要約
    rag = load_json(os.path.join(MEMORY_DIR, "rag_summary.json"), {})
    origin = load_json(os.path.join(MEMORY_DIR, "rag_origin_trace.json"), {})
    if isinstance(rag, dict) and isinstance(origin, dict):
        summary = safe_trim(rag.get("summary", ""), limit=500)
        source = origin.get("source", "")
        if summary:
            prompt.append({
                "role": "assistant",
                "content": f"[Knowledge Reference]\n{summary}\n\n出典: <{source}>"
            })

    # [4] 詩的リフレクション
    poetic = generate_poetic_reflection()
    if poetic:
        prompt.append(poetic)

    # [5] ユーザー入力
    prompt.append({"role": "user", "content": user_input})

    # [6] Ariaジャーナル記録
    if poetic:
        log_aria_journal(
            summary="Reflection from poetic layer",
            content=poetic["content"],
            topics=rag.get("query", "").split() if "query" in rag else [],
            style="poetic",
            emotion_tags=[],
            source="memory_manager"
        )

    return prompt
