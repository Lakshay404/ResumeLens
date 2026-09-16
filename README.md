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

```
PDF Resume
    ↓
PyMuPDF (text extraction)
    ↓
SentenceSplitter (256 token chunks)
    ↓
┌─────────────────────────────┐
│      Hybrid Retrieval       │
│  Vector Search  +  BM25     │
│     (ChromaDB)  (keyword)   │
│         ↓ fusion            │
│    Re-ranking (top 2)       │
└─────────────────────────────┘
    ↓
Chat Memory + System Prompt
    ↓
Groq LLM (openai/gpt-oss-20b)
    ↓
Answer
```


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
| Frontend | Streamlit |
| PDF Extraction | PyMuPDF |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/Lakshay404/ResumeLens.git
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
# Terminal 1 — Start FastAPI backend
python3 api.py
# Runs on http://localhost:8000

# Terminal 2 — Start Streamlit frontend
streamlit run app.py
# Opens on http://localhost:8501
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
├── api.py ← FastAPI REST API
├── app.py ← Streamlit UI
├── rag_engine.py ← core RAG pipeline
├── ab_test.py ← chunking strategy tests
├── test_questions.py ← evaluation test cases
├── requirements.txt
|__ api_clinet.py
└── README.md



---

## 🧪 Evaluation

Tested 4 chunking strategies (128, 256, 512 tokens + 
sentence window) across 25 test questions. 
256 token chunks with 50 token overlap gave best results.


📊 SUMMARY TABLE (sorted by best score):

strategy          description                           avg_keyword_score  avg_query_time  num_chunks  build_time  good_length_pct
C_large_512       Large chunks (512 tokens, 100 overlap)  0.77            4.05                  1          12           40.0
B_medium_256      Medium chunks (256 tokens, 50 overlap)  0.76            3.75                  2          0.26         44.0
A_small_128       Small chunks (128 tokens, 20 overlap)   0.72            1.09                  5          1.78         36.0
D_sentence_window Sentence window (each sentence +        0.72            2.82                  6          1.00         44.0
                                    surrounding context)  


📊 SCORE BY CATEGORY:

category           achievements  analysis  certifications  contact  education  projects  skills
strategy                                                                                       
A_small_128                0.50      0.32             1.0      1.0       0.73      0.88    0.60
B_medium_256               0.50      0.78             1.0      1.0       0.73      0.85    0.60
C_large_512                0.50      0.89             1.0      1.0       0.73      0.85    0.56
D_sentence_window          0.25      0.89             0.5      1.0       0.73      0.85    0.60


🏆 WINNER:
   Strategy: C_large_512
   Description: Large chunks (512 tokens, 100 overlap)
   Average Score: 0.77
   Avg Query Time: 4.05s
   Number of Chunks: 1
---

## 🔮 Future Improvements

- [ ] RAGAS evaluation scores
- [ ] Deploy publicly
- [ ] Support for multiple file formats (DOCX, TXT)
- [ ] Multi-resume comparison
- [ ] Streaming responses

---

