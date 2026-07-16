# test_retrieval.py
import os
import tiktoken
import lancedb
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# 1. Configuration & Setup
DB_PATH = os.environ.get("LANCEDB_PATH", "./lancedb_data")
api_key = "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"

print("=== NEURAL HORIZONS: LANCEDB SEMANTIC QUERY TEST ===")

# Initialize the exact same embedding model used during ingestion
embedder = NVIDIAEmbeddings(
    nvidia_api_key="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", 
    model="nvidia/nv-embedqa-e5-v5", 
    truncate="END"
)

# Connect to the persistent database volume
db = lancedb.connect(DB_PATH)
table = db.open_table("enterprise_knowledge")

# Initialize Tokenizer for budget auditing
tokenizer = tiktoken.get_encoding("cl100k_base")
CONTEXT_BUDGET_LIMIT = 1500

def run_evaluation_query(query_text: str):
    """
    Embeds the user query, searches LanceDB, and audits the token budget.
    """
    print(f"\n[QUERY] \"{query_text}\"")
    
    # 1. Embed the search query
    query_vector = embedder.embed_query(query_text)
    
    # 2. Perform Vector Similarity Search (fetching top 3 closest matches)
    results = table.search(query_vector).limit(3).to_list()
    
    if not results:
        print("[RESULT] No matching context found in the database.")
        return

    total_retrieved_tokens = 0
    
    for i, res in enumerate(results):
        score = res.get('_distance', 'N/A')
        doc_type = res.get('doc_type', 'UNKNOWN')
        tokens = res.get('token_count', 0)
        source = res.get('source_file', 'UNKNOWN')
        
        total_retrieved_tokens += tokens
        
        print(f"  --> Match {i+1} | Score (Distance): {score:.4f} | Type: [{doc_type}] | Source: {source}")
    
    # 3. Context Budget Auditing
    print(f"\n[TOKEN CHECK] Total Context Length: {total_retrieved_tokens} tokens / {CONTEXT_BUDGET_LIMIT} budget limit")
    
    if total_retrieved_tokens <= CONTEXT_BUDGET_LIMIT:
        print("[STATUS] PASS - Context is within safe injection boundaries.")
    else:
        print("[STATUS] FAIL - Context exceeds budget! Truncation required in coordinator_agent.py.")

if __name__ == "__main__":
    # Test 1: Targeting a 512-token Standard Operating Procedure
    run_evaluation_query("How do I fix db-server-01 when it runs out of disk space?")
    
    # Test 2: Targeting a 1024-token Technical API Schema
    run_evaluation_query("What are the payload requirements and forbidden commands for the system mutation API?")
