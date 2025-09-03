import os, re, uuid, shutil, httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_utils import search_chunks, unique_files, upsert_chunks
from document_parser import parse_to_chunks

# ----- Config -----
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

app = FastAPI(title="RAG Chatbot")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class AskReq(BaseModel):
    query: str
    top_k: int = 5

GENERIC_Q = re.compile(r"^(что это|что за файл|о чём файл|what is it|about file)\b", re.I)

# ----- LLM helper -----
async def ollama_chat(messages: list[dict], timeout=120) -> str:
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        )
        if r.status_code != 200:
            raise HTTPException(502, f"Ollama error {r.status_code}: {r.text}")
        return r.json().get("message", {}).get("content", "").strip()

# ----- Health -----
@app.get("/llm/health")
async def llm_health():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{OLLAMA_URL}/api/tags")
        return {"ok": r.status_code == 200, "status": r.status_code, "body": r.text[:300]}

# ----- Upload  -----
from typing import Optional, List


def _ext(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()

async def _save_and_parse(one: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dst = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{_ext(one.filename)}")
    content: bytes = await one.read()
    with open(dst, "wb") as out:
        out.write(content)
    size = len(content)
    chunks, ftype, full_text = parse_to_chunks(dst)

    result = {
        "name": one.filename,
        "saved_as": dst,
        "bytes": size,
        "ftype": ftype,
        "chunks": len(chunks),
        "ok": bool(chunks),
    }

    if not chunks:
        result.update({
            "error": "no_text_extracted",
            "preview": (content[:200].decode("utf-8", "ignore") if content else "")
        })
        return result, None  # не индексируем

    
    prompt = "Сделай краткое резюме файла (2–4 предложения): тема, назначение, ключевые разделы.\n\n" + full_text[:4000]
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{OLLAMA_URL}/api/generate",
                             json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
            summary = r.json().get("response", "").strip() or full_text[:500]
    except Exception:
        summary = full_text[:500]

    upsert_chunks(
        chunks,
        {"file_name": one.filename, "file_type": ftype, "summary": summary, "source": dst}
    )
    return result, len(chunks)

@app.post("/upload")
async def upload(
    file: Optional[UploadFile] = File(default=None),
    files: Optional[List[UploadFile]] = File(default=None),
):
    """
    Принимает ИЛИ single `file`, ИЛИ multiple `files` (как на твоём фронте сейчас).
    Возвращает сводку по каждому файлу.
    """
    batch: List[UploadFile] = []
    if files:
        batch = list(files)
    elif file:
        batch = [file]

    if not batch:
        return {
            "ok": False,
            "error": "no_file_field",
            "hint": "Ожидались поля 'file' или 'files' (multipart/form-data)."
        }

    results = []
    total_chunks = 0
    for one in batch:
        res, added = await _save_and_parse(one)
        results.append(res)
        if added:
            total_chunks += added

    ok_any = any(r.get("ok") for r in results)
    return {
        "ok": ok_any,
        "files": len(results),
        "indexed_chunks": total_chunks,
        "files_list": [r["name"] for r in results],
        "details": results,
    }


# ----- Ask -----
@app.post("/ask")
async def ask(req: AskReq):
    hits = search_chunks(req.query, top_k=req.top_k)
    good = [h for h in hits if h.get("text")]

    if not good or GENERIC_Q.search(req.query):
        files = unique_files(limit=10)
        if files:
            lines = []
            sources = []
            for f in files:
                name = f.get("file_name") or "?"
                ftype = f.get("file_type") or "?"
                summary = (f.get("summary") or "").strip() or "(нет краткого описания)"
                lines.append(f"- {name} ({ftype}): {summary}")
                sources.append(name)
            return {"answer": "Загруженные файлы:\n" + "\n".join(lines), "sources": sources, "used_model": "direct"}
        return {"answer": "Данные ещё не загружены. Добавьте файл и повторите вопрос.", "sources": [], "used_model": "direct"}

    context = "\n- ".join(h["text"] for h in good)
    messages = [
        {"role": "system", "content": "Ты RAG-ассистент. Используй ТОЛЬКО предоставленные фрагменты. Если ответа нет — скажи об этом."},
        {"role": "user", "content": f"Вопрос: {req.query}\n\nФрагменты:\n- {context}"}
    ]
    answer = await ollama_chat(messages)
    sources = [h["file_name"] for h in good if h.get("file_name")]
    return {"answer": answer or "В загруженных материалах ответа не нашёл.", "sources": sources, "used_model": OLLAMA_MODEL}

# ----- Parsers debug -----
@app.get("/debug/parsers")
def parsers():
    def has(mod):
        try:
            __import__(mod)
            return True
        except Exception:
            return False
    # отдельная проверка для pdfminer
    try:
        from pdfminer.high_level import extract_text as _t  # noqa
        pdfminer_ok = True
    except Exception:
        pdfminer_ok = False
    return {
        "PyMuPDF_fitz": has("fitz"),
        "pdfminer.six": pdfminer_ok,
        "python-docx": has("docx"),
        "docx2txt": has("docx2txt"),
        "mammoth": has("mammoth"),
        "pillow": has("PIL"),
        "pytesseract": has("pytesseract"),
    }

# ----- Root -----
@app.get("/")
def root():
    return {"ok": True, "endpoints": ["/llm/health", "/upload", "/ask", "/debug/parsers"]}

