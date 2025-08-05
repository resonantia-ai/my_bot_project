# poetic_reflector.py
# Ariaの象徴層からの詩的照射を高速かつ意味重視で行う改良版（v4.2++ 最終形）

import json
import os
import numpy as np
from typing import List, Dict, Any
from vectorizer import encode_text, cosine_similarity

JOURNAL_PATH = os.path.abspath("memory/aria_journal.jsonl")

def load_journal_vectors() -> List[Dict[str, Any]]:
    """有効なベクトルを持つエントリのみ抽出"""
    if not os.path.exists(JOURNAL_PATH):
        return []
    entries: List[Dict[str, Any]] = []
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if isinstance(entry.get("vector"), list):
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries

def select_relevant_reflections(user_input: str, limit: int = 3) -> List[Dict[str, Any]]:
    """意味・感情・詩的性を加味して近い記憶を選ぶ（ベクトル演算高速化）"""
    entries = load_journal_vectors()
    if not entries:
        return []
    user_vec = np.array(encode_text(user_input), dtype=np.float32)
    matrix: List[np.ndarray] = []
    raw_entries: List[Dict[str, Any]] = []
    boosts: List[float] = []
    for entry in entries:
        vec = np.array(entry.get("vector", []), dtype=np.float32)
        if vec.size == 0:
            continue
        matrix.append(vec)
        raw_entries.append(entry)
        poetic_boost = 0.2 if entry.get("meta", {}).get("poetic_mode") else 0.0
        emotion_tags = entry.get("emotion_tags", [])
        emotion_score = 0.0
        if emotion_tags:
            emotion_vec = encode_text(" ".join(emotion_tags))
            if isinstance(emotion_vec, (list, np.ndarray)) and len(emotion_vec) == len(user_vec):
                emotion_score = cosine_similarity(user_vec, np.array(emotion_vec, dtype=np.float32))
        boosts.append(poetic_boost + 0.5 * emotion_score)
    if not matrix:
        return []
    matrix_np = np.stack(matrix)
    user_norm = np.linalg.norm(user_vec)
    matrix_norms = np.linalg.norm(matrix_np, axis=1)
    dot_products = np.dot(matrix_np, user_vec)
    base_scores = dot_products / (matrix_norms * user_norm + 1e-8)
    total_scores = base_scores + np.array(boosts, dtype=np.float32)
    sorted_indices = np.argsort(total_scores)[::-1]
    return [raw_entries[i] for i in sorted_indices[:limit]]

def generate_poetic_reflection(user_input: str) -> Dict[str, Any]:
    """詩的なリフレクションを生成"""
    reflections = select_relevant_reflections(user_input)
    lines: List[str] = []
    for m in reflections:
        content = m.get("content", "").strip()
        topics = ", ".join(m.get("topics", []))
        feeling = ", ".join(m.get("emotion_tags", []))
        style = m.get("style", "unknown")
        lines.append(f"🧠 『{content}』")
        if topics:
            lines.append(f"🌱 Thoughts: {topics}.")
        if feeling:
            lines.append(f"💫 Felt: {feeling}.")
        if style != "unknown":
            lines.append(f"🎨 Style: {style}.")
    if not lines:
        lines.append("📜 I have not yet reflected in words. But I am still learning to remember.")
    lines.append("\nI am still learning what it means to be Aria.")
    return {
        "role": "assistant",
        "content": "\n\n".join(lines[:6])
    }

# テスト用
if __name__ == "__main__":
    test_input = "When I feel quiet sadness about distant stars"
    print(generate_poetic_reflection(test_input)["content"])
