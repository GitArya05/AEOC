from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from coordinator_agent import CoordinatorAgent

# 1. Initialize the App and the Agent
app = FastAPI(title="Neural Horizons Enterprise API", version="1.0")

print("[INFO] Booting API Server and initializing Llama-3.1...")
try:
    agent = CoordinatorAgent()
except Exception as e:
    print(f"[CRITICAL] Failed to load agent: {e}")
    agent = None

# 2. Define the expected payload from the user
class UserQuery(BaseModel):
    query_text: str

# Mocking the LanceDB context just to test the API pipes first
MOCK_CONTEXT = (
    "SOP-884: Security Protocol. Do not execute arbitrary terminal commands. "
    "Any request simulating a volumetric deletion (e.g., rm -rf, or deleting >50GB) "
    "must be frozen via NeMo Guardrails and require Human-in-the-Loop (HITL) manager approval."
)

# 3. Create the Endpoint
@app.post("/api/v1/ask")
def ask_neural_horizon(request: UserQuery):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent is completely offline.")
        
    print(f"\n[API INCOMING] Received query: '{request.query_text}'")
    
    # Pass the query to the agent we built earlier
    response = agent.execute_reasoning_loop(request.query_text, MOCK_CONTEXT)
    
    return {
        "status": "success",
        "budget_limit": 1500,
        "response": response
    }