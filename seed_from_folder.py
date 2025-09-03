import os, sys, httpx, asyncio
from qdrant_utils import upsert_chunks
from document_parser import parse_to_chunks

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

async def summarize(text: str, max_chars=4000) -> str:
    chunk = (text or "").strip()[:max_chars]
    if not chunk: return ""
    prompt = "Сделай краткое резюме файла в 2–4 предложениях: тема, назначение, ключевые разделы.\n\n" + chunk
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{OLLAMA_URL}/api/generate",
                             json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
            if r.status_code == 200:
                return r.json().get("response", "").strip()
    except Exception:
        pass
    return chunk[:500]

async def main(folder: str):
    total_chunks = 0
    files = 0
    for root, _, fnames in os.walk(folder):
        for fname in fnames:
            if fname.startswith("~$"):  # временные docx
                continue
            path = os.path.join(root, fname)
            chunks, ftype, full_text = parse_to_chunks(path)
            summary = await summarize(full_text)
            upsert_chunks(
                chunks,
                meta={"file_name": fname, "file_type": ftype, "summary": summary, "source": path},
            )
            total_chunks += len(chunks)
            files += 1
            print(f"Indexed {len(chunks)} chunks from {fname} ({ftype})")
    print(f"Done. Files: {files}, chunks: {total_chunks}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_from_folder.py <folder_path>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
