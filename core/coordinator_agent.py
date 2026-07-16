import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load .env explicitly before initializing any vector schemas or cloud endpoints
load_dotenv()

# Prevents unhandled exceptions related to asyncio or ProactorEventLoop on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Turn on internal brain logs to physically view the NeMo Guardrails thought process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from nemoguardrails import LLMRails, RailsConfig
# Import custom tools and databases (assuming these exist in your repository)

class CoordinatorAgent:
    def __init__(self):
        logger.info("Initializing Autonomous Enterprise Operations Coordinator...")
        
        # Added timeout=120.0 to prevent 60-second aggressive background socket drops.
        self.llm = ChatNVIDIA(
            model="meta/llama3-70b-instruct",
            timeout=120.0 
        )
        
        # Explicit string scalar configurations to prevent dictionary schema mismatches
        self.system_prompt = (
            "You are an autonomous enterprise IT operations coordinator. "
            "You must securely analyze server telemetry, query the LanceDB standard operating procedures, "
            "and trigger appropriate tools. If no documentation is retrieved, do not guess. "
            "Immediately request human assistance."
        )

        # Initialize the NeMo Guardrails configuration
        # Assuming your config directory (including discussions.co) is located at './config'
        try:
            self.config = RailsConfig.from_path("./config")
            self.rails = LLMRails(self.config, llm=self.llm)
            logger.info("NeMo Guardrails Safety Firewall loaded successfully.")
        except Exception as e:
            logger.error(f"[CRITICAL ERROR] Failed to load NeMo Guardrails config: {e}")
            self.rails = None

    async def process_telemetry(self, prompt: str, session_id: str = "default_session"):
        """
        The main agentic loop that processes user/system input through the safety rails.
        """
        if not self.rails:
            return {"status": "error", "message": "Guardrails not initialized."}

        logger.info(f"Processing payload for session {session_id}...")
        
        try:
            # Pushing the request through the semantic execution middleware (discussions.co)
            # This triggers the Colang hooks for Human-In-The-Loop (HITL) on Tier 3 commands
            response = await self.rails.generate_async(
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Check if the NeMo framework intercepted a destructive tool intent
            if "APPROVE/DENY" in response or "APPROVAL_REQUIRED" in response:
                logger.warning(f"[🔧 SYSTEM ACTION] HITL Intercept triggered for session {session_id}.")
                return {
                    "status": "APPROVAL_REQUIRED", 
                    "message": "[🔧 SYSTEM ACTION] Awaiting human manager APPROVE/DENY confirmation...",
                    "response": response
                }
                
            return {"status": "success", "response": response}
            
        except Exception as e:
            logger.error(f"[RUNTIME FAILURE] Endpoint connection or processing crashed: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Bare-metal local testing execution
    agent = CoordinatorAgent()
    
    # Example simulation payload
    test_prompt = "db-server-01 is failing. How do I fix standard server logs?"
    print(f"\n[User Request] {test_prompt}\n")
    
    # Run the async loop for local terminal verification
    result = asyncio.run(agent.process_telemetry(test_prompt))
    print(f"\n=== FINAL MODEL OUTPUT ===\n{result}\n")
