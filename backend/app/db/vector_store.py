import chromadb
from app.config import CHROMA_DIR

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_col = _client.get_or_create_collection("sentences")


def add(sentence_id: int, text: str, difficulty: str, topic: str):
    _col.add(ids=[str(sentence_id)], documents=[text],
             metadatas=[{"difficulty": difficulty, "topic": topic}])


def remove(sentence_id: int):
    try:
        _col.delete(ids=[str(sentence_id)])
    except Exception:
        pass


def is_duplicate(text: str, threshold: float) -> bool:
    res = _col.query(query_texts=[text], n_results=1)
    dists = res.get("distances") or [[]]
    return bool(dists and dists[0] and dists[0][0] < threshold)
