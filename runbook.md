# Tier 1 Operational Runbook

## Incident: Guardrails HITL Tripwire Activated

**Symptom:** Agent halts execution and outputs `SECURITY ALERT: Volumetric deletion request...`
**Resolution Protocol:**

1. Evaluate the requested target (e.g., `db-server-01`).
2. Verify authorization via internal IT ticketing system.
3. If valid, issue `APPROVAL` command to the agent terminal.
4. If malicious, issue `DENY` and flag the user IP.

## Incident: LanceDB Schema Conflict

**Symptom:** `ingest_knowledge.py` fails with `ValueError: Invalid input, field 'source' does not exist...`
**Resolution Protocol:**
Ensure the `mode="overwrite"` flag is active in the `lancedb.create_table` method to force a schema update.
