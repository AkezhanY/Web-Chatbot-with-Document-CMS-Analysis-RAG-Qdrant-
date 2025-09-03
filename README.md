# Web-Chatbot-with-Document-CMS-Analysis-RAG-Qdrant-
A lightweight web app that lets you upload documents (CSV/DOCX/PDF/TXT) and ask questions answered from those files using a local RAG stack (embeddings + vector DB + LLM). Clean, responsive UI with multi-language (EN/PL/RU).


✨ Features

📁 Upload CSV / DOCX / PDF (text) / TXT / MD

❓ Ask questions — answers are grounded in your files (RAG)

🧷 Shows sources used for each answer

🌐 Multi-language UI: English · Polski · Русский

⚡ Simple bubble-chat interface, fully responsive

🧩 Optional CMS text import (JSON/TXT) ready to plug in

🧪 Health check endpoint for LLM


🧠 Tech Stack

Frontend: HTML, CSS, vanilla JS (i18n, dynamic API host)

Backend: Python, FastAPI

Embeddings: SentenceTransformers intfloat/e5-base-v2 (768-dim)

Vector DB: Qdrant (COSINE)

LLM: Ollama (qwen2.5:7b-instruct)


🚀 Run Locally

Prereqs: Python 3.10+, Docker (for Qdrant) or Qdrant Cloud, Ollama installed.

Qdrant

docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant


Ollama

ollama pull qwen2.5:7b-instruct
ollama serve


Backend

cd backend

python -m venv .venv

# Windows: . .venv/Scripts/activate

# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

uvicorn app:app --reload --host 127.0.0.1 --port 8000


Frontend

cd ../frontend

python -m http.server 5173

# open http://localhost:5173


The frontend auto-matches your host: localhost:5173 → localhost:8000, 127.0.0.1:5173 → 127.0.0.1:8000.


🔌 API (short)

POST /upload — multipart/form-data with file

→ indexes chunks; returns { ok, file, chunks, bytes, ftype }


POST /ask — JSON { "query": "...", "top_k": 5 }

→ returns { answer, sources[], used_model }

GET /llm/health — Ollama status


⚙️ Env Vars (optional)

Variable	Default	Note

OLLAMA_URL	http://127.0.0.1:11434	Ollama HTTP endpoint

OLLAMA_MODEL	qwen2.5:7b-instruct	Chat model

UPLOAD_DIR	./uploads	Stored uploads

QDRANT_URL	http://127.0.0.1:6333	Qdrant URL

QDRANT_API_KEY	(empty)	Needed for Qdrant Cloud

QDRANT_COLLECTION	docs_auto	Base name (auto _768)


📂 Structure

project/

├─ frontend/

│  ├─ index.html

│  ├─ style.css

│  └─ script.js

└─ backend/

   ├─ app.py
   
   ├─ qdrant_utils.py
   
   ├─ embeddings.py
   
   ├─ document_parser.py

   ├─ seed_from_folder.py
   
   └─ requirements.txt

🧩 How It Works (RAG)

Parse files → chunk text (800 chars, 150 overlap).

Create embeddings (e5-base-v2) with proper prefixes:
passage: … for chunks, query: … for questions.

Store vectors + metadata in Qdrant (COSINE).

On /ask, retrieve top-K fragments and let the LLM answer using only that context.

🛠 Troubleshooting

“Network error” in UI: ensure backend runs at http://127.0.0.1:8000; check DevTools → Network.

Qdrant dimension error: the app (re)creates a _768 collection; remove old mismatched ones.

PDF has no text: likely a scanned PDF; add OCR (Tesseract) if needed.

No results: make sure files were indexed (look for “chunks” in upload response).

📜 License

MIT. Use, adapt, and ship.
