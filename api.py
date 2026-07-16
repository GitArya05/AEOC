from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn
from typing import Optional

# Import the core agent you just fixed
from coordinator_agent import CoordinatorAgent

# Initialize the FastAPI application
app = FastAPI(
    title="Autonomous Enterprise Operations Coordinator",
    description="Team Neural Horizons Track A APIs",
    version="1.0.0"
)

# Initialize the global agent instance
agent = CoordinatorAgent()

# -------------------------------------------------------------------
# Pydantic Schemas for JSON Validation
# -------------------------------------------------------------------
class ChatRequest(BaseModel):
    prompt: str
    session_id: str

class ChatResponse(BaseModel):
    status: str
    session_id: str
    response: Optional[str] = None
    proposed_action: Optional[str] = None

class ApprovalWebhook(BaseModel):
    session_id: str
    decision: str  # e.g., "APPROVE" or "DENY"

# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Accepts standard infrastructure health requests and triggers the agent brain.
    """
    try:
        # Pass the HTTP POST payload string into the single async function
        result = await agent.execute_workflow(request.prompt)
        
        # Check if the NeMo Guardrails tripwire intercepted a destructive command
        if result.get("status") == "APPROVAL_REQUIRED":
            return ChatResponse(
                status="APPROVAL_REQUIRED",
                session_id=request.session_id,
                proposed_action=result.get("proposed_action", "unknown_action")
            )
            
        return ChatResponse(
            status="SUCCESS",
            session_id=request.session_id,
            response=result.get("output", "Task completed.")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Endpoint connection or processing crashed: {str(e)}"
        )

@app.post("/approve")
async def approval_webhook(request: ApprovalWebhook):
    """
    The secondary webhook endpoint where the UI dashboard sends the manual approval token.
    """
    if request.decision.upper() not in ["APPROVE", "DENY"]:
        raise HTTPException(status_code=400, detail="Decision must be APPROVE or DENY")
        
    try:
        # This function would wake the agent back up, retrieve its state, and execute the tool
        # Assuming agent.resolve_approval is implemented in coordinator_agent.py
        resolution_result = await agent.resolve_approval(request.session_id, request.decision.upper())
        return {"status": "SUCCESS", "message": "Action executed successfully.", "details": resolution_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# Server Execution
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Expose FastAPI endpoints on port 8000
    uvicorn.run("api.py:app", host="0.0.0.0", port=8000, reload=True)
