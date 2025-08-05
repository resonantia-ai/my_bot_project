# vectorizer.py
# テキストを意味ベクトル（数値リスト）に変換するベクトライザーモジュール


from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

# モデル読み込み（軽量 or 高性能モデルに切替可能）
MODEL_NAME = "all-MiniLM-L6-v2"  # 384次元で高速
_model = SentenceTransformer(MODEL_NAME)

def encode_text(text: str) -> List[float]:
    """
    入力テキストをエンコードして意味ベクトル（list of float）を返す
    """
    if not text.strip():
        return []
    try:
        embedding = _model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"[vectorizer] encode_textエラー: {e}")
        return []

def cosine_similarity(vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
    """
    2つのベクトル間のコサイン類似度を返す（-1〜1）
    """
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
            return 0.0
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    except Exception as e:
        print(f"[vectorizer] cosine_similarityエラー: {e}")
        return 0.0

def batch_encode(texts: List[str]) -> List[List[float]]:
    """
    複数テキストを一括でエンコード（list[str] → list[list[float]]）
    """
    if not texts:
        return []
    try:
        return _model.encode(texts, convert_to_numpy=True).tolist()
    except Exception as e:
        print(f"[vectorizer] batch_encodeエラー: {e}")
        return []
