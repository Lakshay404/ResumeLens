# api.py
# FastAPI REST API for Resume RAG

import os
import uuid
import shutil
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from rag_engine import build_index, load_chat_engine

load_dotenv()

# ── App Setup ─────────────────────────────────────────────────
app = FastAPI(
    title="Resume RAG API",
    description="Upload a resume and ask questions about it using RAG + Hybrid Search + Re-ranking",
    version="1.0.0"
)

# Allow requests from any frontend (browser, mobile, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── In-memory session store ────────────────────────────────────
# Stores chat engines per session
# In production: use Redis instead
sessions: Dict[str, object] = {}

# Folder to store uploaded resumes
UPLOAD_DIR = "./uploaded_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Request/Response Models ────────────────────────────────────

class QuestionRequest(BaseModel):
    session_id: str
    question: str

class QuestionResponse(BaseModel):
    session_id: str
    question: str
    answer: str

class UploadResponse(BaseModel):
    session_id: str
    message: str
    num_chunks: int
    text_length: int

class SessionInfo(BaseModel):
    session_id: str
    active: bool

class HealthResponse(BaseModel):
    status: str
    message: str
    active_sessions: int


# ── Routes ────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Resume RAG API is running",
        active_sessions=len(sessions)
    )


@app.get("/health", response_model=HealthResponse)
def health():
    """Detailed health check."""
    return HealthResponse(
        status="healthy",
        message="All systems operational",
        active_sessions=len(sessions)
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF.
    Returns a session_id to use for all future questions.

    - Accepts: PDF files only
    - Returns: session_id, chunk count, text length
    """

    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a .pdf file."
        )

    # Generate unique session ID for this resume
    session_id = str(uuid.uuid4())

    # Save uploaded file
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    pdf_path = os.path.join(session_dir, file.filename)
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Build index
    try:
        result = build_index(
            pdf_path=pdf_path,
            collection_name=session_id,
            persist_path=session_dir
        )
    except ValueError as e:
        # Clean up if indexing fails
        shutil.rmtree(session_dir)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        shutil.rmtree(session_dir)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process resume: {str(e)}"
        )

    # Load chat engine into memory for this session
    try:
        chat_engine = load_chat_engine(
            persist_path=session_dir,
            collection_name=session_id
        )
        sessions[session_id] = {
            "engine": chat_engine,
            "pdf_path": pdf_path,
            "filename": file.filename
        }
    except Exception as e:
        shutil.rmtree(session_dir)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chat engine: {str(e)}"
        )

    return UploadResponse(
        session_id=session_id,
        message=f"Resume '{file.filename}' processed successfully. Use session_id for questions.",
        num_chunks=result["num_chunks"],
        text_length=result["text_length"]
    )


@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded resume.

    - Requires: session_id from /upload endpoint
    - Supports: follow-up questions (chat memory enabled)
    - Uses: Hybrid Search + Re-ranking pipeline
    """

    # Check session exists
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{request.session_id}' not found. Please upload a resume first via /upload."
        )

    # Validate question
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Get answer
    try:
        chat_engine = sessions[request.session_id]["engine"]
        response = chat_engine.chat(request.question)
        answer = str(response)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )

    return QuestionResponse(
        session_id=request.session_id,
        question=request.question,
        answer=answer
    )


@app.delete("/session/{session_id}", response_model=SessionInfo)
def delete_session(session_id: str):
    """
    Delete a session and free up memory.
    Call this when done with a resume.
    """

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found."
        )

    # Remove from memory
    del sessions[session_id]

    # Remove files from disk
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)

    return SessionInfo(
        session_id=session_id,
        active=False
    )


@app.get("/sessions")
def list_sessions():
    """
    List all active sessions.
    Useful for debugging.
    """
    return {
        "active_sessions": len(sessions),
        "session_ids": [
            {
                "session_id": sid,
                "filename": data["filename"]
            }
            for sid, data in sessions.items()
        ]
    }


# ── Run Server ────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True      # auto-restarts on code changes
    )