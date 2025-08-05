# rag_engine.py
# 意味語抽出→未知語確認→Wikipedia / ORKG / DBpedia / arXiv / Wikidataから照射→記録まで一括


import os
import json
import requests
from yake import KeywordExtractor
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import List, Tuple, Optional

# === ファイルパス（絶対パス化） ===
MEMORY_DIR = os.path.abspath("memory")
SUMMARY_PATH = os.path.join(MEMORY_DIR, "rag_summary.json")
ORIGIN_TRACE_PATH = os.path.join(MEMORY_DIR, "rag_origin_trace.json")
JOURNAL_PATH = os.path.join(MEMORY_DIR, "aria_journal.json")
LONG_TERM_PATH = os.path.join(MEMORY_DIR, "compressed_memory.json")

# === キーワード抽出 ===
def extract_keywords(text: str, lang: Optional[str] = None) -> List[str]:
    lang = lang or ("ja" if any("\u3000" <= c <= "\u9fff" for c in text) else "en")
    extractor = KeywordExtractor(lan=lang, n=2, top=3)
    return [kw[0] for kw in extractor.extract_keywords(text)]

# === 未知語判定（ジャーナル + 圧縮記憶）===
def is_new_term(keyword: str) -> bool:
    sources = []
    for path in [JOURNAL_PATH, LONG_TERM_PATH]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sources += [entry.get("content", "") for entry in data if isinstance(entry, dict)]
            except Exception as e:
                print(f"[RAG] {path}読込エラー: {e}")
    return all(keyword.lower() not in src.lower() for src in sources)

# === 各種照射API ===
def fetch_from_wikipedia(query: str) -> Tuple[Optional[str], Optional[str]]:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Stellabiblia-RAG/1.0"})
        if resp.status_code == 200:
            d = resp.json()
            return d.get("extract", ""), d.get("content_urls", {}).get("desktop", {}).get("page", "")
    except Exception as e:
        print(f"[Wiki] {e}")
    return None, None

def fetch_from_orkg(query: str) -> Tuple[Optional[str], Optional[str]]:
    url = f"https://www.orkg.org/api/papers?query={query}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("content"):
                p = d["content"][0]
                return p.get("title", "") + "\n\n" + p.get("research_fields", [{}])[0].get("label", ""), p.get("url", "")
    except Exception as e:
        print(f"[ORKG] {e}")
    return None, None

def fetch_from_dbpedia(query: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        sparql = SPARQLWrapper("https://dbpedia.org/sparql")
        sparql.setQuery(f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT ?abstract WHERE {{
                dbr:{query.replace(' ', '_')} dbo:abstract ?abstract .
                FILTER(lang(?abstract)='en')
            }}
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        b = results["results"]["bindings"]
        if b:
            return b[0]["abstract"]["value"], f"https://dbpedia.org/resource/{query.replace(' ', '_')}"
    except Exception as e:
        print(f"[DBpedia] {e}")
    return None, None

def fetch_from_arxiv(query: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=1"
        resp = requests.get(url, headers={"User-Agent": "Stellabiblia-RAG/1.0"})
        if resp.status_code == 200 and "<title>" in resp.text:
            t = resp.text
            title = t.split("<title>")[1].split("</title>")[0].strip()
            link = t.split("<id>")[1].split("</id>")[0].strip()
            return title, link
    except Exception as e:
        print(f"[arXiv] {e}")
    return None, None

def fetch_from_wikidata(query: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        url = "https://www.wikidata.org/w/api.php"
        resp = requests.get(url, params={
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json"
        })
        if resp.status_code == 200:
            d = resp.json().get("search", [])
            if d:
                return d[0].get("description", ""), d[0].get("concepturi", "")
    except Exception as e:
        print(f"[Wikidata] {e}")
    return None, None

# === ルーティング判定 ===
def route_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    kws = query.lower().split()
    if any(k in kws for k in ["quantum", "neural", "embedding", "reasoning"]):
        return fetch_from_arxiv(query)
    if any(k in kws for k in ["philosophy", "ontology", "ai", "structure"]):
        return fetch_from_orkg(query)
    if any(k in kws for k in ["symbol", "representation", "definition", "concept"]):
        return fetch_from_dbpedia(query)
    if any(k in kws for k in ["data", "entity", "name", "date"]):
        return fetch_from_wikidata(query)
    return fetch_from_wikipedia(query)

# === メイン関数（全体処理）===
def fetch_and_store_rag(text: str) -> Optional[str]:
    keywords = extract_keywords(text)
    for word in keywords:
        if is_new_term(word):
            summary, url = route_query(word)
            if summary:
                try:
                    os.makedirs(MEMORY_DIR, exist_ok=True)
                    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                        json.dump({"query": word, "summary": summary}, f, ensure_ascii=False, indent=2)
                    with open(ORIGIN_TRACE_PATH, "w", encoding="utf-8") as f:
                        json.dump({"query": word, "source": url}, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"[RAG] 保存エラー: {e}")
                return summary
    return None

# === テスト用 ===
if __name__ == "__main__":
    result = fetch_and_store_rag("symbolic reasoning")
    print(result or "❌ No summary")
