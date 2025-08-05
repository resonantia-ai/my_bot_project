
from flask import Flask, request, jsonify
from llama_cpp import Llama
import os
from typing import Any

app = Flask(__name__)


# モデルパス（絶対パス化）
model_path = os.path.abspath("model/Phi-4-mini-instruct.Q4_K_S.gguf")

# プロンプト読み込み（絶対パス化）
prompt_path = os.path.abspath("prompts/aria_prompt.txt")
try:
    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()
except Exception as e:
    print(f"[server] プロンプト読み込みエラー: {e}")
    base_prompt = ""

# モデル初期化
try:
    llm = Llama(model_path=model_path, n_ctx=2048, n_threads=6)
except Exception as e:
    print(f"[server] モデル初期化エラー: {e}")
    llm = None


@app.route("/v1/chat/completions", methods=["POST"])
def chat() -> Any:
    if llm is None or not base_prompt:
        return jsonify({"error": "Model or prompt not loaded."}), 500
    try:
        data = request.json
        user_msg = data["messages"][-1]["content"]
        prompt = f"{base_prompt}\n<|user|>\n{user_msg}\n<|assistant|>\n"
        output = llm(prompt, temperature=0.7, max_tokens=1024)
        response_text = output["choices"][0]["text"].strip()
        return jsonify({
            "choices": [{"message": {"content": response_text}}]
        })
    except Exception as e:
        print(f"[server] 応答生成エラー: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=1234)
