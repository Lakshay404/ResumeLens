import os
import logging

import streamlit as st

from api_client import ApiError, ask_question, check_health, delete_session, upload_resume

st.set_page_config(
    page_title="Resume Chatbot",
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #eef6ff 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SUGGESTED_QUESTIONS = [
    "What are the key technical skills?",
    "What is the educational background?",
    "Summarize the work experience.",
    "What are the notable projects?",
]


def initialize_session_state():
    defaults = {
        "session_id": None,
        "messages": [],
        "uploaded_filename": None,
        "upload_complete": False,
        "num_chunks": None,
        "text_length": None,
        "pending_question": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def clear_visible_chat():
    st.session_state.messages = []


def reset_to_upload():
    if st.session_state.get("session_id"):
        try:
            delete_session(st.session_state.session_id)
        except ApiError as exc:
            st.warning(f"Session cleanup warning: {exc}")

    for key in [
        "session_id",
        "messages",
        "uploaded_filename",
        "upload_complete",
        "num_chunks",
        "text_length",
    ]:
        st.session_state[key] = None if key != "messages" else []
    st.session_state.upload_complete = False


def submit_question(question: str):
    cleaned = (question or "").strip()
    if not cleaned:
        st.warning("Please enter a question first.")
        return

    if not st.session_state.get("session_id"):
        st.warning("Please upload a resume before asking questions.")
        return

    with st.chat_message("user"):
        st.markdown(cleaned)

    st.session_state.messages.append({"role": "user", "content": cleaned})

    thinking_placeholder = st.empty()
    with thinking_placeholder.container():
        st.markdown("Thinking...")
        with st.spinner(""):
            try:
                response = ask_question(st.session_state.session_id, cleaned)
                answer = response.get("answer", "")
            except ApiError as exc:
                thinking_placeholder.empty()
                st.error(str(exc))
                return
            except Exception as exc:
                thinking_placeholder.empty()
                logging.getLogger(__name__).exception("Unexpected ask_question failure")
                st.error("Something went wrong while generating the answer.")
                return

    thinking_placeholder.empty()

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


def render_upload_screen():
    st.title("📄 Resume Chatbot")
    st.markdown("### Chat with your resume using AI")
    st.caption("Upload your resume and ask anything about your skills, experience, or fit for a role.")

    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"],
        label_visibility="collapsed",
        help="Only PDF files are supported.",
    )

    if uploaded_file is not None:
        st.write("")
        if st.button("Upload and Start Chatting →", use_container_width=True):
            try:
                with st.spinner("Processing resume..."):
                    payload = upload_resume(uploaded_file)

                st.session_state.session_id = payload["session_id"]
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.upload_complete = True
                st.session_state.num_chunks = payload.get("num_chunks")
                st.session_state.text_length = payload.get("text_length")
                st.success(f"Resume uploaded successfully: {uploaded_file.name}")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
            except Exception:
                logging.getLogger(__name__).exception("Upload failed")
                st.error("Failed to upload the resume. Please try again.")

    st.write("")
    st.info("The backend processes the PDF, builds the index, and prepares the chat session before you can ask questions.")


def render_chat_screen():
    st.title("📄 Resume Chatbot")

    col_title, col_action = st.columns([5, 1])
    with col_title:
        st.markdown(f"### Resume: {st.session_state.uploaded_filename or 'Current resume'}")
    with col_action:
        if st.button("New Resume", use_container_width=True):
            reset_to_upload()
            st.rerun()

    status_text = "✅ Ready to chat"
    if st.session_state.num_chunks is not None:
        status_text += f"  •  Chunks: {st.session_state.num_chunks}"
    if st.session_state.text_length is not None:
        status_text += f"  •  Characters: {st.session_state.text_length}"

    st.markdown(
        f"<p style='margin: 0 0 1rem 0; color: #16a34a; font-size: 1rem; font-weight: 600;'>{status_text}</p>",
        unsafe_allow_html=True,
    )

    st.write("")

    messages_container = st.container()
    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with st.container():
        st.write("**Suggested questions**")
        cols = st.columns(2)
        for idx, question in enumerate(SUGGESTED_QUESTIONS):
            with cols[idx % 2]:
                if st.button(question, key=f"suggested-{idx}"):
                    st.session_state.pending_question = question

    if st.session_state.get("pending_question"):
        question_to_submit = st.session_state.pending_question
        st.session_state.pending_question = None
        submit_question(question_to_submit)

    st.write("")
    prompt = st.chat_input("Ask anything about the resume...")
    if prompt:
        submit_question(prompt)

    if st.session_state.messages:
        st.write("")
        if st.button("Clear Chat"):
            clear_visible_chat()
            st.rerun()


initialize_session_state()

with st.sidebar:
    st.markdown("### API Status")
    try:
        health = check_health()
        st.success(f"Backend online: {health.get('status', 'healthy')}")
    except ApiError as exc:
        st.warning(f"Backend unavailable: {exc}")
    except Exception:
        st.warning("Could not connect to the backend API.")

    st.markdown("---")
    st.caption("API base URL")
    st.code(os.getenv("API_BASE_URL", "http://localhost:8000"))

    if st.session_state.get("upload_complete") and st.session_state.get("session_id"):
        if st.button("Delete Current Session"):
            try:
                delete_session(st.session_state.session_id)
                st.session_state.session_id = None
                st.session_state.upload_complete = False
                st.session_state.messages = []
                st.session_state.uploaded_filename = None
                st.session_state.num_chunks = None
                st.session_state.text_length = None
                st.success("Session deleted successfully.")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))

if st.session_state.get("upload_complete"):
    render_chat_screen()
else:
    render_upload_screen()
