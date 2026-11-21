import hashlib
import json
import re
from pathlib import Path
from threading import Lock
from uuid import uuid4
from backend.config import settings

_lock = Lock()
_client = None
_collection = None
_encoder = None

def store():
    global _client, _collection, _encoder
    with _lock:
        if _collection is None:
            import chromadb
            from sentence_transformers import SentenceTransformer
            root = settings.boris_data_dir
            (root / "vectorstore").mkdir(parents=True, exist_ok=True)
            _encoder = SentenceTransformer(settings.embedding_model)
            _client = chromadb.PersistentClient(path=str(root / "vectorstore"))
            _collection = _client.get_or_create_collection("boris_knowledge", metadata={"hnsw:space": "cosine"})
    return _collection, _encoder

def extract(filename: str, content: bytes):
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        try:
            return [(i+1, page.get_text()) for i, page in enumerate(doc)]
        finally:
            doc.close()
    if ext == ".docx":
        from io import BytesIO
        from docx import Document
        doc = Document(BytesIO(content))
        return [(1, "\n".join(x.text for x in doc.paragraphs))]
    if ext in {".txt", ".md", ".csv"}:
        return [(1, content.decode("utf-8-sig", errors="replace"))]
    raise ValueError("Unsupported file type. Use PDF, DOCX, TXT, MD, or CSV")

def chunk(text, size=700, overlap=100):
    words = text.split()
    stride = size - overlap
    return [" ".join(words[i:i+size]) for i in range(0, len(words), stride) if words[i:i+size]]

def ingest(filename: str, content: bytes):
    if len(content) > 15*1024*1024:
        raise ValueError("File exceeds 15MB limit")
    if not Path(filename).suffix.lower() in {".pdf", ".docx", ".txt", ".md", ".csv"}:
        raise ValueError("Unsupported file type")
    pages = extract(filename, content)
    items = [(page, ch) for page, text in pages for ch in chunk(text)]
    if not items:
        raise ValueError("No extractable text found; scanned PDFs require OCR (not in MVP)")
    digest = hashlib.sha256(content).hexdigest()
    root = settings.boris_data_dir / "raw"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{digest}{Path(filename).suffix.lower()}").write_bytes(content)
    col, enc = store()
    ids = [f"{digest}-{i}" for i in range(len(items))]
    col.upsert(ids=ids, documents=[t for _,t in items], embeddings=enc.encode([t for _,t in items], normalize_embeddings=True).tolist(), metadatas=[{"filename": filename, "page": page, "sha256": digest, "chunk": i} for i,(page,_) in enumerate(items)])
    return {"document_id": digest, "filename": filename, "chunks": len(items)}

def retrieve(query: str, top_k=5):
    col, enc = store()
    if col.count() == 0:
        return []
    result = col.query(query_embeddings=enc.encode([query], normalize_embeddings=True).tolist(), n_results=min(max(top_k*3,top_k),col.count()), include=["documents","metadatas","distances"])
    docs = []
    for id_, txt, meta, dist in zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]):
        docs.append({"id":id_, "text":txt, "filename":meta["filename"], "page":meta["page"], "score":round(1-float(dist),4)})
    # Hybrid rank: semantic ranking plus lexical overlap; RRF-style fusion.
    tokens = set(re.findall(r"\w+",query.lower()))
    semantic = {d["id"]:i for i,d in enumerate(docs)}
    lexical = sorted(docs,key=lambda d:len(tokens & set(re.findall(r"\w+",d["text"].lower()))),reverse=True)
    lexical_rank = {d["id"]:i for i,d in enumerate(lexical)}
    return sorted(docs,key=lambda d:1/(60+semantic[d["id"]])+1/(60+lexical_rank[d["id"]]),reverse=True)[:top_k]

def list_docs():
    col,_=store()
    if col.count()==0:return []
    result=col.get(include=["metadatas"])
    by_id={}
    for meta in result["metadatas"]:
        by_id[meta["sha256"]]={"document_id":meta["sha256"],"filename":meta["filename"]}
    return list(by_id.values())

def delete_doc(doc_id):
    col,_=store()
    ids=col.get(where={"sha256":doc_id})["ids"]
    if ids:col.delete(ids=ids)
    return len(ids)
