# 1. EARLY ENVIRONMENT INITIALIZATION
from dotenv import load_dotenv
load_dotenv()  # Must be on line 1 to catch NVAPI_KEY before schema initialization

import os
import time
import logging
import pyarrow as pa
import lancedb
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure internal logging to monitor the batching pipeline
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 2. CONFIGURATION & THRESHOLDS
LANCEDB_PATH = os.getenv("LANCEDB_PATH", "./lancedb_data")
TABLE_NAME = "enterprise_runbooks"
BATCH_SIZE = 500  # Crucial: Prevents Out-Of-Memory (OOM) crashes during the 15k file load

class KnowledgeIngestor:
    def __init__(self):
        logger.info("Initializing LanceDB Data Engine...")
        # Connect to the local/volume-mounted LanceDB instance
        self.db = lancedb.connect(LANCEDB_PATH)
        
        # Initialize NVIDIA's high-performance embedding model
        try:
            self.embedder = NVIDIAEmbeddings(model="NV-Embed-QA")
            logger.info("NVIDIA NIM Embedding engine connected successfully.")
        except Exception as e:
            logger.error(f"[CRITICAL] Failed to authenticate NVIDIA Embeddings. Check NVAPI_KEY: {e}")
            raise

        # 3. DUAL-TIER CHUNKING STRATEGY (Arya's Architecture)
        # 512 tokens for dense SOPs to prevent context hallucination
        self.sop_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512, 
            chunk_overlap=50
        )
        # 1024 tokens for API Schemas to preserve JSON/Code structures
        self.api_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, 
            chunk_overlap=100
        )

    def define_schema(self):
        """Defines the PyArrow schema required for LanceDB vector storage."""
        # Assuming NV-Embed-QA outputs 1024-dimensional vectors. 
        # Adjust 'list_size' if using a different embedding model size.
        return pa.schema([
            pa.field("vector", pa.list_(pa.float32(), 1024)),
            pa.field("text", pa.string()),
            pa.field("document_type", pa.string()),
            pa.field("source", pa.string())
        ])

    def process_and_ingest(self, document_payloads):
        """
        Processes raw document dictionaries, chunks them, generates embeddings, 
        and writes them to LanceDB in optimized batches.
        """
        schema = self.define_schema()
        
        # Create or open the table
        if TABLE_NAME not in self.db.table_names():
            table = self.db.create_table(TABLE_NAME, schema=schema)
            logger.info(f"Created new LanceDB table: {TABLE_NAME}")
        else:
            table = self.db.open_table(TABLE_NAME)
            logger.info(f"Opened existing LanceDB table: {TABLE_NAME}")

        total_docs = len(document_payloads)
        logger.info(f"Starting ingestion pipeline for {total_docs} documents...")

        # 4. MEMORY-SAFE BATCH PROCESSING
        for i in range(0, total_docs, BATCH_SIZE):
            batch = document_payloads[i:i + BATCH_SIZE]
            rows_to_insert = []

            logger.info(f"Processing Batch {i // BATCH_SIZE + 1} (Documents {i} to {i + len(batch)})...")
            
            for doc in batch:
                # Select the appropriate chunking strategy based on metadata
                if doc.get("type") == "API_SCHEMA":
                    chunks = self.api_splitter.split_text(doc["content"])
                else:
                    chunks = self.sop_splitter.split_text(doc["content"])

                # Generate embeddings for the chunks via NVIDIA NIM
                try:
                    embeddings = self.embedder.embed_documents(chunks)
                    
                    # Map chunks to the PyArrow schema structure
                    for chunk_text, embedding in zip(chunks, embeddings):
                        rows_to_insert.append({
                            "vector": embedding,
                            "text": chunk_text,
                            "document_type": doc.get("type", "SOP"),
                            "source": doc.get("source", "unknown")
                        })
                except Exception as e:
                    logger.warning(f"Failed to embed document {doc.get('source')}: {e}")
                    continue

            # Push the compiled batch to the local LanceDB disk
            if rows_to_insert:
                table.add(rows_to_insert)
                logger.info(f"Successfully wrote {len(rows_to_insert)} vectorized chunks to disk.")
                time.sleep(0.5) # Slight throttle to prevent API rate limiting

        logger.info("✅ Ingestion Pipeline Complete. Database is ready for Retrieval (RAG).")

if __name__ == "__main__":
    # --- MOCK DATA GENERATION FOR LOCAL TESTING ---
    # In production, this would read your ~15,000 synthetic files from a directory
    logger.info("Loading dummy compliance and telemetry data for pipeline test...")
    
    mock_documents = [
        {
            "content": "SOP for db-server-01: If storage exceeds 95%, execute clear_server_logs tool immediately.",
            "type": "SOP",
            "source": "manuals/db_operations.txt"
        },
        {
            "content": "API Schema for network_router: {\"endpoint\": \"/api/v1/reset\", \"method\": \"POST\", \"auth\": \"required\"}",
            "type": "API_SCHEMA",
            "source": "schemas/network_api.json"
        }
    ] * 250 # Multiplying to simulate a batch of 500 documents

    # Execute Pipeline
    ingestor = KnowledgeIngestor()
    ingestor.process_and_ingest(mock_documents)
