FROM python:3.11-slim

WORKDIR /app

# Copy minimal requirements and install dependencies
COPY requirements/kafka-producer.txt ./requirements/kafka-producer.txt
RUN pip install --no-cache-dir -r requirements/kafka-producer.txt

# Copy application code
COPY pipeline/__init__.py pipeline/
COPY pipeline/producer/ pipeline/producer/
COPY pipeline/ticker/ pipeline/ticker/

# Set Python path to include pipeline modules
ENV PYTHONPATH=/app

# Run the kafka producer
CMD ["python", "-m", "pipeline.producer.main"]