# =======================================================================
# STAGE 1: THE BUILDER 
# Purpose: Installs heavy C++ compilers (gcc, g++) to build LanceDB 
# and NeMo Guardrails dependencies cleanly.
# =======================================================================
FROM python:3.11-slim AS builder

# Set the working directory for the build process
WORKDIR /build

# Update apt and install the required OS-level C++ compilers
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the builder
COPY requirements.txt .

# Install all Python dependencies into a specific /install prefix directory.
# This prevents installing them globally in the builder, making them easy to copy.
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# =======================================================================
# STAGE 2: THE SLIM RUNNER (FINAL IMAGE)
# Purpose: A lightweight, secure footprint that leaves the compilers behind.
# This is what actually deploys to the cloud.
# =======================================================================
FROM python:3.11-slim AS runner

# Set the working directory for the runtime application
WORKDIR /app

# Safely copy ONLY the compiled python packages from the builder stage
COPY --from=builder /install /usr/local

# Force Python to print logs immediately (crucial for seeing Agentic thought loops)
ENV PYTHONUNBUFFERED=1

# =======================================================================
# PERSISTENT MEMORY & ISOLATION
# Create the LanceDB volume mount point so the ~15,000 document vectors 
# are not wiped out if the container crashes or restarts.
# =======================================================================
RUN mkdir -p /app/lancedb_data
VOLUME ["/app/lancedb_data"]

# Copy the microservice source code into the container
COPY core/ ./core/
COPY config/ ./config/
COPY api.py .

# Expose the network port for the enterprise microservice dashboard
EXPOSE 8000

# Trigger the FastAPI wrapper when the container boots
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]