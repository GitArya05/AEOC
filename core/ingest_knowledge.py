import os
import lancedb
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from pipeline_validator import validate_synthetic_payload 

print("=== NEURAL HORIZONS: ENTERPRISE INGESTION PIPELINE ===")

# 1. Secure API Key Loading (Enterprise Standard)
load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    raise ValueError("[CRITICAL] NVIDIA_API_KEY not found. Please ensure your .env file is set up correctly.")

print("[INFO] Booting NVIDIA NIM Embedding connection...")
embedder = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    nvidia_api_key=api_key,
    truncate="END"
)

# Boot LanceDB
db = lancedb.connect("./lancedb_data")

# 2. Read the Synthetic Data Stream
source_dir = "raw_documentation"
if not os.path.exists(source_dir):
    raise FileNotFoundError(f"[CRITICAL] Folder '{source_dir}' not found. Run generate_synthetic_data.py first.")

all_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
files_to_process = all_files[:50] 
print(f"[INFO] Routing {len(files_to_process)} raw files through the Pydantic Shield...")

valid_documents = []

# 3. Validation Phase
for filename in files_to_process:
    filepath = os.path.join(source_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    doc_id = filename.replace(".txt", "")
    
    raw_payload = {
        "document_id": doc_id,
        "text_content": raw_text,
        "doc_type": "LOG" if "REPORT" in filename else "SOP",
        "source_stream_id": 14 
    }
    
    validated_doc = validate_synthetic_payload(raw_payload)
    
    if validated_doc:
        valid_documents.append(validated_doc)

print(f"\n[STATUS] Shield caught {(len(files_to_process) - len(valid_documents))} malformed payloads.")
print(f"[STATUS] Pushing {len(valid_documents)} clean documents into the embedding queue...\n")

# 4. Chunking & Bulk Embedding Phase
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
all_rows = []

for doc in valid_documents:
    chunks = text_splitter.split_text(doc.text_content)
    
    for chunk_text in chunks:
        vector = embedder.embed_query(chunk_text)
        
        all_rows.append({
            "vector": vector,
            "text": chunk_text,
            "source": doc.document_id,
            "type": doc.doc_type
        })
        
    print(f"[SUCCESS] Processed chunks for {doc.document_id}.")

# 🚀 THE FIX: Bulk overwrite forces LanceDB to accept the new schema
table = db.create_table("enterprise_knowledge", data=all_rows, mode="overwrite")

print("\n=== INGESTION COMPLETE ===")
print(f"Total new vector rows appended to LanceDB: {len(all_rows)}")