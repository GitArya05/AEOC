from pydantic import BaseModel, Field, ValidationError
from typing import Optional

# 1. The Strict Mapping Schema
class DocumentSchema(BaseModel):
    document_id: str
    text_content: str = Field(..., min_length=10, description="Raw synthetic text must have actual content.")
    doc_type: str = Field(..., pattern="^(SOP|API_SCHEMA|LOG)$", description="Must be an approved document type.")
    source_stream_id: int = Field(default=1, ge=1, le=60, description="Must map to one of the 60 active heterogeneous data streams.")

# 2. The Safety Catch (Prevents Pipeline Crashes)
def validate_synthetic_payload(raw_payload: dict) -> Optional[DocumentSchema]:
    """
    Checks incoming raw data. If it breaks the schema, it logs a warning 
    instead of throwing a fatal error, keeping the pipeline alive.
    """
    try:
        # Attempt to map the raw data to our strict schema
        clean_doc = DocumentSchema(**raw_payload)
        print(f"[PIPELINE PASS] Stream {clean_doc.source_stream_id} | Document {clean_doc.document_id} mapped successfully.")
        return clean_doc
    
    except ValidationError as e:
        # here it will avoid the pipleine from being crashed.
        error_msg = e.errors()[0]['msg']
        failed_id = raw_payload.get('document_id', 'UNKNOWN_ID')
        print(f"[PIPELINE DROPPED] Bad data caught for ID: {failed_id}. Reason: {error_msg}")
        return None  # Returning None means the pipeline skips this row instead of crashing

# ==========================================
# 3. Local Test: Proving the Pipeline Holds
# ==========================================
if __name__ == "__main__":
    print("=== SYNTHETIC DATA PIPELINE VALIDATION TEST ===\n")
    
    # Payload A: Perfect Data
    good_synthetic_data = {
        "document_id": "SOP-1042",
        "text_content": "This is a clean, formatted payload for the system mutation API.",
        "doc_type": "API_SCHEMA",
        "source_stream_id": 14
    }
    
    # Payload B: Broken Data (Wrong type, text too short, invalid stream number)
    bad_synthetic_data = {
        "document_id": "ERR-9999",
        "text_content": "bug", 
        "doc_type": "RANDOM_JUNK", 
        "source_stream_id": 99 
    }
    
    print("Testing Clean Data Stream:")
    validated_good = validate_synthetic_payload(good_synthetic_data)
    
    print("\nTesting Broken Data Stream (Should NOT trigger an error crash):")
    validated_bad = validate_synthetic_payload(bad_synthetic_data)