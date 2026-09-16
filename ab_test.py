# ab_test.py
# Tests 4 different chunking strategies and compares their performance

import os
import time
import glob
import fitz
import pickle
import pandas as pd
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from llama_index.core.node_parser import (
    SentenceSplitter,
    SentenceWindowNodeParser
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from test_questions import TEST_CASES

load_dotenv()

# ── Setup ─────────────────────────────────────────────────────

print("=" * 60)
print("A/B CHUNKING STRATEGY TEST")
print("=" * 60)

# Load resume text
pdf_files = glob.glob("./data/*.pdf")
doc = fitz.open(pdf_files[0])
full_text = ""
for page in doc:
    full_text += page.get_text()
doc.close()

print(f"✅ Resume loaded: {len(full_text)} characters\n")

# Load models (shared across all strategies)
print("🔢 Loading models...")
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)
Settings.llm = llm
Settings.embed_model = embed_model

reranker = FlagEmbeddingReranker(
    model="BAAI/bge-reranker-base",
    top_n=2
)
print("✅ Models ready\n")

# ── Define 4 Chunking Strategies ──────────────────────────────

STRATEGIES = {

    "A_small_128": {
        "description": "Small chunks (128 tokens, 20 overlap)",
        "parser": SentenceSplitter(
            chunk_size=128,
            chunk_overlap=20
        )
    },

    "B_medium_256": {
        "description": "Medium chunks (256 tokens, 50 overlap)",
        "parser": SentenceSplitter(
            chunk_size=256,
            chunk_overlap=50
        )
    },

    "C_large_512": {
        "description": "Large chunks (512 tokens, 100 overlap)",
        "parser": SentenceSplitter(
            chunk_size=512,
            chunk_overlap=100
        )
    },

    "D_sentence_window": {
        "description": "Sentence window (each sentence + surrounding context)",
        "parser": SentenceWindowNodeParser.from_defaults(
            window_size=3,           # include 3 sentences around each sentence
            window_metadata_key="window",
            original_text_metadata_key="original_text"
        )
    }
}

# ── Helper Functions ───────────────────────────────────────────

def build_query_engine(strategy_name, parser, documents):
    """Build a fresh query engine for each strategy."""

    # Create nodes using this strategy's chunking
    nodes = parser.get_nodes_from_documents(documents)

    # Fresh ChromaDB collection for each strategy
    chroma_client = chromadb.EphemeralClient()  # in-memory, no disk
    collection = chroma_client.get_or_create_collection(strategy_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Build index
    index = VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model
    )

    # Hybrid retriever
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

    # Query engine with reranker
    query_engine = RetrieverQueryEngine.from_args(
        retriever=hybrid_retriever,
        node_postprocessors=[reranker],
        llm=llm
    )

    return query_engine, len(nodes)


def evaluate_answer(answer, expected_keywords):
    """
    Simple evaluation:
    Check how many expected keywords appear in the answer.
    Returns a score from 0.0 to 1.0
    """
    answer_lower = answer.lower()
    found = sum(
        1 for kw in expected_keywords
        if kw.lower() in answer_lower
    )
    return round(found / len(expected_keywords), 2)


def measure_answer_length_quality(answer):
    """
    Checks if answer is:
    - Too short (< 10 words) → probably didn't find anything
    - Too long (> 100 words) → probably hallucinating / padding
    - Just right (10-100 words) → good
    """
    words = len(answer.split())
    if words < 10:
        return "too_short"
    elif words > 100:
        return "too_long"
    else:
        return "good"


# ── Run the Tests ─────────────────────────────────────────────

documents = [Document(text=full_text)]
all_results = []

for strategy_name, config in STRATEGIES.items():

    print(f"\n{'─' * 60}")
    print(f"Testing Strategy {strategy_name}")
    print(f"Description: {config['description']}")
    print(f"{'─' * 60}")

    # Build engine for this strategy
    print("Building index...")
    build_start = time.time()
    query_engine, num_chunks = build_query_engine(
        strategy_name,
        config["parser"],
        documents
    )
    build_time = round(time.time() - build_start, 2)
    print(f"✅ Index built: {num_chunks} chunks in {build_time}s")

    # Run all test questions
    strategy_scores = []

    for i, test_case in enumerate(TEST_CASES):
        question = test_case["question"]
        expected = test_case["expected_keywords"]
        category = test_case["category"]

        print(f"\n  Q{i+1} [{category}]: {question[:50]}...")

        # Time the query
        query_start = time.time()
        try:
            response = query_engine.query(question)
            answer = str(response)
            query_time = round(time.time() - query_start, 2)

            # Evaluate
            keyword_score = evaluate_answer(answer, expected)
            length_quality = measure_answer_length_quality(answer)

            print(f"  Answer: {answer[:80]}...")
            print(f"  Score: {keyword_score} | Length: {length_quality} | Time: {query_time}s")

            strategy_scores.append({
                "strategy": strategy_name,
                "description": config["description"],
                "question": question,
                "category": category,
                "answer": answer,
                "keyword_score": keyword_score,
                "length_quality": length_quality,
                "query_time": query_time,
                "num_chunks": num_chunks,
                "build_time": build_time
            })

        except Exception as e:
            print(f"  ❌ Error: {e}")
            strategy_scores.append({
                "strategy": strategy_name,
                "description": config["description"],
                "question": question,
                "category": category,
                "answer": f"ERROR: {e}",
                "keyword_score": 0,
                "length_quality": "error",
                "query_time": 0,
                "num_chunks": num_chunks,
                "build_time": build_time
            })

        # Small delay to avoid rate limiting
        time.sleep(1)

    all_results.extend(strategy_scores)
    avg_score = sum(s["keyword_score"] for s in strategy_scores) / len(strategy_scores)
    print(f"\n  ✅ Strategy {strategy_name} average score: {avg_score:.2f}")


# ── Generate Report ───────────────────────────────────────────

print("\n\n" + "=" * 60)
print("RESULTS REPORT")
print("=" * 60)

df = pd.DataFrame(all_results)

# Summary table — one row per strategy
summary = df.groupby(["strategy", "description"]).agg(
    avg_keyword_score=("keyword_score", "mean"),
    avg_query_time=("query_time", "mean"),
    num_chunks=("num_chunks", "first"),
    build_time=("build_time", "first"),
    good_length_pct=("length_quality",
                     lambda x: round((x == "good").mean() * 100, 1))
).reset_index()

summary["avg_keyword_score"] = summary["avg_keyword_score"].round(2)
summary["avg_query_time"] = summary["avg_query_time"].round(2)

# Sort by best score
summary = summary.sort_values("avg_keyword_score", ascending=False)

print("\n📊 SUMMARY TABLE (sorted by best score):\n")
print(summary.to_string(index=False))

# Per-category breakdown
print("\n\n📊 SCORE BY CATEGORY:\n")
category_breakdown = df.groupby(
    ["strategy", "category"]
)["keyword_score"].mean().unstack().round(2)
print(category_breakdown.to_string())

# Winner
best_strategy = summary.iloc[0]
print("\n\n🏆 WINNER:")
print(f"   Strategy: {best_strategy['strategy']}")
print(f"   Description: {best_strategy['description']}")
print(f"   Average Score: {best_strategy['avg_keyword_score']}")
print(f"   Avg Query Time: {best_strategy['avg_query_time']}s")
print(f"   Number of Chunks: {best_strategy['num_chunks']}")

# Save full results to CSV
df.to_csv("ab_test_results.csv", index=False)
print(f"\n✅ Full results saved to: ab_test_results.csv")
print("\n💡 Update your ingest.py to use the winning chunk size!")