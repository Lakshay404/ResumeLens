# rag_engine.py
# Shared RAG logic used by both api.py and app.py

import os
import glob
import fitz
import pickle
from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb





def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()


    return full_text


def build_index(pdf_path: str, collection_name: str, persist_path: str):
    """
    Build vector index + BM25 nodes from a PDF.
    Saves to persist_path/chroma_db and persist_path/nodes.pkl
    """

    # Extract text
    full_text = extract_text_from_pdf(pdf_path)
    if len(full_text) < 50:
        raise ValueError("Could not extract text from PDF. File may be image-based or protected.")

    # Wrap in document
    documents = [Document(
        text=full_text,
        metadata={"filename": os.path.basename(pdf_path)}
    )]

    # Load models
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    llm = Groq(
        model="openai/gpt-oss-20b",
        api_key=os.getenv("GROQ_API_KEY")
    )
    Settings.llm = llm
    Settings.embed_model = embed_model

    # Chunk document
    splitter = SentenceSplitter(chunk_size=256, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    # Build ChromaDB index
    os.makedirs(persist_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(
        path=os.path.join(persist_path, "chroma_db")
    )
    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model
    )

    # Save BM25 nodes
    nodes_path = os.path.join(persist_path, "nodes.pkl")
    with open(nodes_path, "wb") as f:
        pickle.dump(nodes, f)

    return {
        "num_chunks": len(nodes),
        "text_length": len(full_text),
        "persist_path": persist_path
    }


def load_chat_engine(persist_path: str, collection_name: str):
    """
    Load a chat engine from a previously built index.
    Returns a fresh chat engine with memory.
    """

    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    llm = Groq(
        model="openai/gpt-oss-20b",
        api_key=os.getenv("GROQ_API_KEY")
    )
    Settings.llm = llm
    Settings.embed_model = embed_model

    # Load ChromaDB
    chroma_client = chromadb.PersistentClient(
        path=os.path.join(persist_path, "chroma_db")
    )
    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
        embed_model=embed_model
    )

    # Load BM25 nodes
    nodes_path = os.path.join(persist_path, "nodes.pkl")
    with open(nodes_path, "rb") as f:
        nodes = pickle.load(f)

    # Build hybrid retriever
    vector_retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=6
    )
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=6
    )
    hybrid_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=6,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False,
        llm=llm
    )

    # Re-ranker
    reranker = FlagEmbeddingReranker(
        model="BAAI/bge-reranker-base",
        top_n=6
    )

    # Memory
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

    # Chat engine
    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=hybrid_retriever,
        llm=llm,
        memory=memory,
        node_postprocessors=[reranker],
        system_prompt=(
            "You are a helpful assistant that answers questions "
            "about a person's resume. Be professional, concise "
            "and accurate. If something is not in the resume, "
            "say so clearly instead of guessing."
        )
    )

    return chat_engine