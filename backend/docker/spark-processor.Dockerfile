# ---------- BUILD STAGE ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (temporarily)
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ python3-dev libffi-dev libblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/spark-processor.txt ./requirements/spark-processor.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements/spark-processor.txt

# Download spaCy model inside build layer
RUN python -m spacy download en_core_web_sm

# ---------- RUNTIME STAGE ----------
FROM python:3.11-slim

WORKDIR /app

# Install only Java + minimal tools
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless procps \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME dynamically
RUN JAVA_PATH=$(find /usr/lib/jvm -name 'java-21-openjdk*' -type d | head -1) && \
    echo "JAVA_HOME=$JAVA_PATH" >> /etc/environment && \
    echo "export JAVA_HOME=$JAVA_PATH" >> /root/.bashrc
ENV PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/lib/jvm/java-21-openjdk-arm64/bin:$PATH

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY pipeline/__init__.py pipeline/
COPY pipeline/processor/ pipeline/processor/
COPY pipeline/ticker/ pipeline/ticker/

# Fix ticker cache directory permissions
RUN mkdir -p pipeline/ticker/data && \
    chmod 755 pipeline/ticker/data && \
    find pipeline/ticker/data -name "*.json" -exec chmod 666 {} \;

# Create checkpoint directory
RUN mkdir -p /tmp/spark-checkpoint-new

# Set Python path to include pipeline modules
ENV PYTHONPATH=/app

CMD ["python", "-m", "pipeline.processor.main"]
