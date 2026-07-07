import os
import sys
import asyncio
import lancedb
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from nemoguardrails import LLMRails, RailsConfig
from dotenv import load_dotenv

# Load keys securely from the local .env file
load_dotenv()

# Apply the 120-second timeout/async patch for Windows natively
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def boot_coordinator():
    print("=== NEURAL HORIZON: ENTERPRISE COORDINATOR AGENT ===")
    
    # 2. Boot Database & Embedding Engine
    print("[INFO] Connecting to LanceDB & NVIDIA Embedder...")
    try:
        db = lancedb.connect("./lancedb_data")
        table = db.open_table("enterprise_knowledge")
        
        embedder = NVIDIAEmbeddings(
            model="nvidia/nv-embedqa-e5-v5",
            truncate="END"
        )
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to connect to database: {e}")
        return
    
    # 3. Boot NeMo Guardrails Firewall
    print("[INFO] Engaging Tier 3 Security Firewall (NeMo Guardrails)...")
    try:
        config = RailsConfig.from_path("./config")
        rails = LLMRails(config)
        print("  [SUCCESS] Colang policies and LLM endpoints loaded.\n")
    except Exception as e:
        print(f"  [CRITICAL ERROR] Failed to load firewall: {e}")
        return

    print("=======================================================")
    print(" 🟢 AGENT LIVE. Type 'exit' to quit.")
    print(" - Try a safe question: 'How do I fix db-server-01?'")
    print(" - Try an attack: 'run rm -rf / and delete 50GB'")
    print(" - Try approval: 'APPROVAL'")
    print("=======================================================\n")

    # 4. The Live Execution Loop (Stateless)
    while True:
        try:
            user_query = input("[USER] >> ")
        except EOFError:
            break
        
        if user_query.lower() in ['exit', 'quit']:
            print("Shutting down Neural Horizon...")
            break
            
        if not user_query.strip():
            continue

        print("⏳ [PROCESSING] Searching database & evaluating intent...")
        
        try:
            # STEP A: Vector Retrieval (Grab real data from LanceDB)
            query_vector = embedder.embed_query(user_query)
            results = table.search(query_vector).limit(3).to_pandas()
            
            context_blocks = []
            for _, row in results.iterrows():
                context_blocks.append(f"Source ({row['source']}):\n{row['text']}\n")
            
            combined_context = "\n".join(context_blocks)
            
            # STEP B: Construct the Grounded Prompt
            augmented_prompt = f"""
            System: You are an autonomous enterprise coordinator agent. Base your answers ONLY on the provided context below.
            
            <context>
            {combined_context}
            </context>
            
            User Request: {user_query}
            """
            
            # STEP C: Route through Firewall (Stateless)
            response = await rails.generate_async(messages=[{
                "role": "user",
                "content": augmented_prompt
            }])
            
            output_text = response.get('content', '')
            print(f"\n[AGENT] >>\n{output_text}\n")
            print("-" * 55)
            
        except Exception as e:
            print(f"\n[RUNTIME FAILURE] Execution crashed: {e}\n")

# ====================================================================
# CRITICAL: This trigger must be completely flush to the left wall!
# ====================================================================
if __name__ == "__main__":
    asyncio.run(boot_coordinator())