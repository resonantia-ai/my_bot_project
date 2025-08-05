# symbolic_reflector.py
# Ariaの構文記憶から象徴的・意味的に再帰的記憶を照射する高速統合リフレクター（v4.2++ symbolic_score対応）

import json
import os
import numpy as np
from typing import List, Dict, Any
from vectorizer import encode_text

VECTOR_PATH = os.path.abspath("memory/vector_memory.json")
JOURNAL_PATH = os.path.abspath("memory/aria_journal.jsonl")

def reflect_vector_relevance(user_input: str, top_k: int = 3) -> List[Dict[str, Any]]:
    if not os.path.exists(VECTOR_PATH):
        return []
    try:
        with open(VECTOR_PATH, "r", encoding="utf-8") as f:
            vector_data = json.load(f)
    except Exception as err:
        print(f"[symbolic_reflector] VECTOR_PATH読込エラー: {err}")
        return []

    user_vec = np.array(encode_text(user_input), dtype=np.float32)
    entries, matrix, boosts = [], [], []

    for entry in vector_data:
        vec = np.array(entry.get("embedding", []), dtype=np.float32)
        if vec.size == 0:
            continue
        entries.append(entry)
        matrix.append(vec)
        boosts.append(float(entry.get("emotion_score", 0.0)))

    if not matrix:
        return []

    matrix_np = np.stack(matrix)
    user_norm = np.linalg.norm(user_vec)
    matrix_norms = np.linalg.norm(matrix_np, axis=1)
    dot_products = np.dot(matrix_np, user_vec)
    base_scores = dot_products / (matrix_norms * user_norm + 1e-8)
    total_scores = base_scores + np.array(boosts, dtype=np.float32)

    sorted_indices = np.argsort(total_scores)[::-1]
    return [entries[i] for i in sorted_indices[:top_k]]

def reflect_journal_relevance(user_input: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """aria_journal.jsonlから象徴性・詩的性・意味的に近い記憶を返す（閾値・加点ロジック明示）"""
    if not os.path.exists(JOURNAL_PATH):
        return []
    entries: List[Dict[str, Any]] = []
    matrix: List[np.ndarray] = []
    boosts: List[float] = []
    try:
        with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    score = float(entry.get("symbolic_score", 0.0))
                    if score < 0.5:
                        continue  # 象徴性が低いものは除外
                    vec = np.array(entry.get("vector", []), dtype=np.float32)
                    if vec.size == 0:
                        continue
                    entries.append(entry)
                    matrix.append(vec)
                    poetic_boost = 0.2 if entry.get("meta", {}).get("poetic_mode") or entry.get("style") == "poetic" else 0.0
                    boosts.append(poetic_boost + score * 0.3)  # 象徴性スコア自体も加点
                except json.JSONDecodeError:
                    continue
    except Exception as err:
        print(f"[symbolic_reflector] JOURNAL_PATH読込エラー: {err}")
        return []
    if not matrix:
        return []
    user_vec = np.array(encode_text(user_input), dtype=np.float32)
    matrix_np = np.stack(matrix)
    user_norm = np.linalg.norm(user_vec)
    matrix_norms = np.linalg.norm(matrix_np, axis=1)
    dot_products = np.dot(matrix_np, user_vec)
    base_scores = dot_products / (matrix_norms * user_norm + 1e-8)
    total_scores = base_scores + np.array(boosts, dtype=np.float32)
    sorted_indices = np.argsort(total_scores)[::-1]
    return [entries[i] for i in sorted_indices[:top_k]]

def recall_symbolic_memories(user_input: str) -> List[Dict[str, Any]]:
    vector_memories = reflect_vector_relevance(user_input)
    symbolic_memories = reflect_journal_relevance(user_input)
    return symbolic_memories + vector_memories
