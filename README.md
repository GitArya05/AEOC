# Neural Horizon: AEOC Backend

An enterprise-grade, retrieval-augmented generation (RAG) system secured by a Tier 3 Semantic Firewall and Human-in-the-Loop (HITL) overrides.

## 🏗️ System Architecture

_(Note: Generate a diagram using Mermaid.js or insert a PNG here showing the flow from User -> FastAPI -> NeMo Guardrails -> LanceDB -> NVIDIA NIM)_

- **Ingestion:** Pydantic-validated payload streaming into LanceDB.
- **Retrieval:** NVIDIA `nv-embedqa-e5-v5` for semantic vector search.
- **Security:** NeMo Guardrails intercepting volumetric deletion/destructive intents.

## 🚀 Setup Instructions

1. **Clone the repository:**
   `git clone https://github.com/your-org/neural-horizon.git`
2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your `NVIDIA_API_KEY`.
3. **Install Dependencies:**
   `pip install -r requirements.txt`
4. **Initialize Database:**
   `python core/ingest_knowledge.py`
5. **Boot the Agent:**
   `python core/coordinator_agent.py`

## 📊 Performance & Token Metrics

- **Processing Latency:** RAG retrieval + Firewall semantic evaluation averages `< 1.2s` on local environment.
- **Token Consumption:**
  - Ingestion: 512-token chunks with 50-token overlap.
  - Inference context budget: Capped at ~1,500 tokens (3 documents per query) to optimize NVIDIA API costs.

## 🛡️ Validation & Pressure Testing

Refer to the `/tests` directory for verification scripts:

- `pipeline_validator.py`: Ensures 0% malformed data enters the LanceDB schema.
- `test_safety.py`: Automated payload injection to verify NeMo Guardrails HITL tripwires.
