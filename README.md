# Web-Chatbot-with-Document-CMS-Analysis-RAG-Qdrant-
A small end-to-end RAG system you can embed into any web page. Users upload files (CSV, DOCX, PDF, TXT/MD), the backend parses and chunks content, creates embeddings, stores them in Qdrant, and answers questions using the most relevant fragments and a local LLM (via Ollama).

Highlights
· Minimal FastAPI backend: /upload, /ask, /llm/health

· Vector DB: Qdrant (local Docker or Cloud)

· Embeddings: Sentence Transformers intfloat/e5-base-v2 (768-dim)

· LLM: Ollama (default model qwen2.5:7b-instruct)

· Plain HTML/CSS/JS frontend with i18n (EN/PL/RU) and a clean “bubble chat” UI

· Works fully offline (except model downloads)

Features

Upload files (.csv, .docx, .pdf (text PDFs), .txt, .md)
Robust parsing for TXT/CSV/PDF(DOC-TEXT)/DOCX, automatic chunking (size 800, overlap 150)
Batch embedding + upsert to Qdrant with payload metadata (file name/type/summary)
RAG: semantic search for top-K fragments → LLM answer grounded in context
Sources list in responses
Frontend language switch (EN/PL/RU) for all labels/placeholders/buttons
Frontend automatically matches API host (localhost vs 127.0.0.1)
Note: scanned PDFs (pure images) are not OCR’d by default. See Troubleshooting.

Stack

Frontend: HTML, CSS, vanilla JS
Backend: Python, FastAPI, httpx
Embeddings: SentenceTransformers intfloat/e5-base-v2 (768-dim)
Vector DB: Qdrant (COSINE)
LLM: Ollama (qwen2.5:7b-instruct by default)
Parsers: pdfminer.six (text PDFs), python-docx, pandas (CSV)

Project Structure
project/
├── frontend/
│   ├── index.html       # chat UI + i18n
│   ├── style.css
│   └── script.js        # upload, ask, i18n, dynamic API host
│
├── backend/
│   ├── app.py           # FastAPI: /upload, /ask, /llm/health
│   ├── qdrant_utils.py  # Qdrant helpers (COSINE, dim=768)
│   ├── embeddings.py    # e5-base-v2, prefixes 'passage:'/'query:'
│   ├── document_parser.py# parsing + chunking
│   └── requirements.txt
│
└── README.md

Prerequisites

Python 3.10+ (works on 3.13)
Docker (to run Qdrant locally) or Qdrant Cloud account
Ollama installed and running
Windows users: C++ Build Tools may be required to build some wheels on first install
