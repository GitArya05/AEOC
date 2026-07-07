# init_db.py
import os
import lancedb
import pyarrow as pa

# Point to the persistent Docker volume we set up in the Dockerfile
DB_PATH = os.environ.get("LANCEDB_PATH", "./lancedb_data")

def initialize_database():
    """
    Initializes the LanceDB instance and enforces the schema for the ~15,000 files.
    """
    print(f"=== NEURAL HORIZONS: DATABASE INITIALIZATION ===")
    print(f"[INFO] Connecting to local LanceDB instance at: {DB_PATH}")
    
    # Connect to the local vector directory
    db = lancedb.connect(DB_PATH)

    # Define the strict PyArrow schema for our RAG data
    # We assume a 1024-dimensional embedding from the NVIDIA NIM embedding models
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 1024)), 
        pa.field("text", pa.string()),
        pa.field("doc_type", pa.string()),     # Tracks if this is an "SOP" or "API_SCHEMA"
        pa.field("token_count", pa.int32()),   # Crucial for Arya's Context Auditing
        pa.field("source_file", pa.string())
    ])

    # Safely create the table if it does not exist
    table_name = "enterprise_knowledge"
    if table_name not in db.table_names():
        db.create_table(table_name, schema=schema)
        print(f"[SUCCESS] Table '{table_name}' created successfully with strict schema.")
    else:
        print(f"[INFO] Table '{table_name}' already exists. Ready for ingestion.")

if __name__ == "__main__":
    initialize_database()