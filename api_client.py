import logging
import os
from typing import Any, Dict, Optional

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
logger = logging.getLogger(__name__)


class ApiError(RuntimeError):
    """Raised for backend API failures with user-friendly messages."""


def _raise_for_status(response: requests.Response, fallback: str = "Request failed.") -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    detail = payload.get("detail") if isinstance(payload, dict) else None
    message = detail or fallback
    raise ApiError(message)


def check_health() -> Dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}/health", timeout=20)
    if response.status_code != 200:
        _raise_for_status(response, "Backend health check failed.")
    return response.json()


def upload_resume(file_obj) -> Dict[str, Any]:
    if file_obj is None:
        raise ApiError("Please select a PDF file first.")

    filename = getattr(file_obj, "name", "resume.pdf")
    if not filename.lower().endswith(".pdf"):
        raise ApiError("Only PDF files are supported.")

    files = {"file": (filename, file_obj.getvalue(), "application/pdf")}
    try:
        response = requests.post(
            f"{API_BASE_URL}/upload",
            files=files,
            timeout=180,
        )
    except requests.RequestException as exc:
        logger.exception("Upload request failed")
        raise ApiError(f"Could not reach the backend API: {exc}") from exc

    if response.status_code != 200:
        _raise_for_status(response, "Failed to process resume.")

    payload = response.json()
    return payload


def ask_question(session_id: Optional[str], question: str) -> Dict[str, Any]:
    if not session_id:
        raise ApiError("No active session. Please upload a resume first.")

    clean_question = (question or "").strip()
    if not clean_question:
        raise ApiError("Question cannot be empty.")

    payload = {"session_id": session_id, "question": clean_question}
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json=payload,
            timeout=180,
        )
    except requests.RequestException as exc:
        logger.exception("Ask request failed")
        raise ApiError(f"Could not reach the backend API: {exc}") from exc

    if response.status_code == 404:
        raise ApiError("Session not found. Please upload the resume again.")
    if response.status_code == 400:
        raise ApiError("Question cannot be empty.")
    if response.status_code != 200:
        _raise_for_status(response, "Failed to generate answer.")

    return response.json()


def delete_session(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"session_id": "", "active": False}

    try:
        response = requests.delete(f"{API_BASE_URL}/session/{session_id}", timeout=30)
    except requests.RequestException as exc:
        logger.exception("Delete session request failed")
        raise ApiError(f"Could not reach the backend API: {exc}") from exc

    if response.status_code == 404:
        raise ApiError("Session not found. It may already be inactive.")
    if response.status_code != 200:
        _raise_for_status(response, "Failed to clear the current session.")

    return response.json()
