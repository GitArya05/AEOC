import os
import random

# Create the destination folder
output_dir = "raw_documentation"
os.makedirs(output_dir, exist_ok=True)

# Sample pools to mix and match for high volume and variation
servers = [f"db-server-{i:02d}" for i in range(1, 21)] + [f"web-app-{i:02d}" for i in range(1, 21)] + [f"api-gateway-{i:02d}" for i in range(1, 11)]
components = ["Memory Allocator", "Log Rotation Service", "SSL Certificate Manager", "Connection Pool", "Docker Daemon Subsystem", "PyArrow Vector Layer"]
statuses = ["CRITICAL", "WARNING", "HEALTHY", "DEGRADED"]
remediations = [
    "Execute log rotation script via bash hook immediately.",
    "Flush the network sockets and re-apply the 120-second timeout patch.",
    "Restart the multi-stage container build process to clear local cache anomalies.",
    "Verify Pydantic validation schema alignments and scale down replica count.",
    "Initialize database checkpointing and isolate the active storage volume."
]

print(f"🚀 Generating 15,000 synthetic operational files inside '{output_dir}'...")

# Generate exactly 15,000 files
for file_id in range(1, 15001):
    server = random.choice(servers)
    component = random.choice(components)
    status = random.choice(statuses)
    remediation = random.choice(remediations)
    
    filename = f"SOP_REPORT_{file_id:05d}_{server}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Generate structured synthetic text content
    content = f"""ENTERPRISE COMPLIANCE RUNBOOK AND TELEMETRY REPORT
==================================================
DOCUMENT ID: REF-{file_id:05d}
TARGET SYSTEM: {server}
SUBSYSTEM: {component}
OPERATIONAL STATUS: [{status}]

METRICS DATA SUMMARY:
--------------------
- CPU Utilization: {random.randint(10, 99)}%
- Memory Bound Size: {random.randint(2, 64)} GB
- Context Window Token Budget: {random.randint(500, 1500)} tokens
- Network Latency: {random.randint(5, 300)}ms

STANDARD OPERATING PROCEDURE (SOP):
----------------------------------
If {server} enters a [{status}] state regarding the {component} module, the autonomous coordinator agent must immediately intercept the event.

REQUIRED REMEDIATION WORKFLOW:
1. Scan local LanceDB vector tables for recent infrastructure schema anomalies.
2. {remediation}
3. If issue persists, halt thread execution path and trigger the Human-In-The-Loop (HITL) safety override tripwire via Colang.

----------------==================----------------
CONFIDENTIAL COMPLIANCE DOCUMENT - PROPERTY OF NEURAL HORIZONS AGENT LABS
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print(f"✅ Success! 15,000 files created successfully in '{output_dir}/'. ready for 'ingest_knowledge.py'!")