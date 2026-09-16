# 🔍 ResumeLens

An AI-powered resume Q&A platform built with RAG 
(Retrieval Augmented Generation). Upload any resume 
and ask questions about it in natural language.

**Live Demo:** [coming soon]

---

## ✨ Features

- **Hybrid Search** — combines vector search (ChromaDB) 
  and keyword search (BM25) for better retrieval
- **Re-ranking** — BAAI/bge-reranker-base reranks 
  retrieved chunks for improved answer quality  
- **Chat Memory** — remembers previous questions 
  for context-aware follow-up answers
- **Multi-user Sessions** — each user gets isolated 
  session with their own resume and conversation
- **REST API** — FastAPI backend with 5 endpoints
- **A/B Tested** — evaluated 4 chunking strategies 
  to find optimal chunk size

---

## 🏗️ Architecture

PDF Resume
↓
PyMuPDF (text extraction)
↓
SentenceSplitter (256 token chunks)
↓
┌─────────────────────────────┐
│ Hybrid Retrieval │
│ Vector Search + BM25 │
│ (ChromaDB) (keyword) │
│ ↓ fusion │
│ Re-ranking (top 2) │
└─────────────────────────────┘
↓
Chat Memory + System Prompt
↓
Groq LLM (openai/gpt-oss-20b)
↓
Answer


---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Framework | LlamaIndex |
| LLM | Groq (free) |
| Embeddings | BAAI/bge-small-en-v1.5 (free, local) |
| Re-ranker | BAAI/bge-reranker-base (free, local) |
| Vector DB | ChromaDB |
| Keyword Search | BM25 |
| Backend API | FastAPI |
| Frontend | React.js |
| PDF Extraction | PyMuPDF |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/lakshayagarwal/ResumeLens.git
cd ResumeLens

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Create .env file
touch .env

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" >> .env
```

### Run

```bash
# Add your resume to /data folder
# Then index it
python3 ingest.py

# Option 1: Streamlit UI
streamlit run app.py

# Option 2: REST API
python3 api.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload resume PDF |
| POST | `/ask` | Ask a question |
| DELETE | `/session/{id}` | Delete session |
| GET | `/sessions` | List active sessions |

### Example Usage

```bash
# Upload resume
curl -X POST http://localhost:8000/upload \
  -F "file=@resume.pdf"

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question": "What are this person skills?"
  }'
```

---

## 📁 Project Structure

ResumeLens/
├── data/ ← add your resume here
├── api.py ← FastAPI REST API
├── app.py ← Streamlit UI
├── rag_engine.py ← core RAG pipeline
├── ingest.py ← PDF indexing script
├── ab_test.py ← chunking strategy tests
├── test_questions.py ← evaluation test cases
├── evaluate.py ← RAGAS evaluation
├── requirements.txt
└── README.md


---

## 🧪 Evaluation

Tested 4 chunking strategies (128, 256, 512 tokens + 
sentence window) across 25 test questions. 
256 token chunks with 50 token overlap gave best results.

---

## 🔮 Future Improvements

- [ ] RAGAS evaluation scores
- [ ] Deploy publicly
- [ ] Support for multiple file formats (DOCX, TXT)
- [ ] Multi-resume comparison
- [ ] Streaming responses

---

