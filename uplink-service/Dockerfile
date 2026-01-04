FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Run the application
# Note: running on port 8001 inside the container
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]