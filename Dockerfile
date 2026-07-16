FROM python:3.11-slim AS builder

# Install system-level C++ compilers required for LanceDB and NeMo Guardrails (annoy)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set up the isolated working directory
WORKDIR /build

# Create a virtual environment to hold the compiled packages cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements and install them into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim

# Set the working directory for the final application
WORKDIR /app

# Copy ONLY the fully compiled virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Ensure the system uses the virtual environment's Python binaries
ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the application files (api.py, scripts, config folders)
COPY . .

# Create the directory for LanceDB persistent storage
RUN mkdir -p /app/lancedb_data

# Expose port 8000 for the FastAPI microservice
EXPOSE 8000

# Boot the FastAPI microservice via Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
